from django.shortcuts import render

# Create your views here.
# enquiries/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from enquiries import ml
from django.db.models import Count
from enquiries.models import Enquiry
import pandas as pd

@api_view(['POST'])
def train_api(request):
    try:
        meta = ml.train_model(model_name=request.data.get('model_name','rf_v1'))
        return Response(meta)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def predict_api(request):
    try:
        out = ml.predict_user(request.data)
        return Response(out)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def trend_api(request):
    """
    returns counts grouped by day (last N days) or by week.
    Query params:
        period=day|week (default=day)
        days=30   (default 30)
    """
    period = request.GET.get('period', 'day')
    days = int(request.GET.get('days', 30))
    qs = Enquiry.objects.all()
    if qs.count() == 0:
        return Response({'trend': []})
    df = pd.DataFrame(list(qs.values('created_at', 'booked')))
    df['created_at'] = pd.to_datetime(df['created_at'])
    end = pd.Timestamp.now()
    start = end - pd.Timedelta(days=days)
    df = df[(df['created_at'] >= start) & (df['created_at'] <= end)]
    if period == 'week':
        df['period'] = df['created_at'].dt.to_period('W').astype(str)
    else:
        df['period'] = df['created_at'].dt.date.astype(str)
    # count total and booked per period
    grouped = df.groupby('period').agg(total=('booked','count'), booked=('booked','sum')).reset_index()
    data = grouped.to_dict(orient='records')
    return Response({'trend': data})

@api_view(['GET'])
def funnel_api(request):
    data = ml.compute_funnel()
    # provide conversion rates
    conv_followups = (data['with_followups']/data['total']*100) if data['total'] else 0
    conv_visit = (data['site_visited']/data['with_followups']*100) if data['with_followups'] else 0
    conv_booked = (data['booked']/data['site_visited']*100) if data['site_visited'] else 0
    return Response({'funnel': data, 'conversions': {'followups_rate': conv_followups, 'visit_from_followups': conv_visit, 'booked_from_visits': conv_booked}})

@api_view(['GET'])
def feature_importance_api(request):
    try:
        top_k = int(request.GET.get('top_k', 10))
        feats = ml.get_feature_importances(top_k)
        return Response({'features': feats})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def generate_report_api(request):
    try:
        txt = ml.generate_report()
        return Response({'report': txt})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# Simple chatbot: very small rule-based/Q&A referencing precomputed stats
@api_view(['POST'])
def chatbot_query_api(request):
    """
    Expects JSON: {'query': 'which city has the most interested buyers'}
    This is a simple intent+keyword matcher that queries DB and ml outputs.
    """
    q = request.data.get('query', '').lower()
    if not q:
        return Response({'answer': 'Please send a query.'}, status=status.HTTP_400_BAD_REQUEST)

    qs = Enquiry.objects.all()
    if qs.count() == 0:
        return Response({'answer': 'No enquiries in the database.'})

    # simple intents/keywords
    if 'which city' in q or 'most interested' in q or ('city' in q and 'interested' in q):
        # compute city with highest number of booked
        df = pd.DataFrame(list(qs.values('city','booked')))
        top = df[df['booked']==1]['city'].value_counts().idxmax()
        cnt = int(df[df['booked']==1]['city'].value_counts().max())
        return Response({'answer': f"The city with the most interested buyers is {top} with {cnt} bookings."})

    if 'trend' in q or 'enquiry trend' in q:
        # quick summary: last 7 days trend
        # reuse trend_api logic
        req = request._request
        req.GET = req.GET.copy()
        req.GET['period'] = 'day'
        req.GET['days'] = '7'
        trend_resp = trend_api(req._request) if False else None  # bypass complexity
        # simpler: compute quickly here
        import pandas as pd
        df = pd.DataFrame(list(qs.values('created_at')))
        df['created_at'] = pd.to_datetime(df['created_at']).dt.date
        counts = df['created_at'].value_counts().sort_index().to_dict()
        return Response({'answer': f"Enquiries over the past days: {counts}"})

    if 'top features' in q or 'influence' in q or 'important features' in q:
        feats = ml.get_feature_importances(top_k=5)
        text = ", ".join([f"{f['feature']} ({f['importance']:.2f})" for f in feats])
        return Response({'answer': f"Top features influencing booking: {text}"})

    # fallback
    return Response({'answer': "Sorry, I couldn't understand. Try 'which city has the most interested buyers' or 'top features' or 'show trend'."})
