from .ml import load_df_from_db
from .models import AIGeneratedReport, FeatureImportance
from datetime import datetime
import json

def generate_report(title=None):
    df = load_df_from_db()
    n = len(df)
    booked_rate = float(df['booked'].mean()) if n>0 else 0.0
    # top cities
    top_cities = df.groupby('city').agg(total=('id','count'), booked=('booked','sum')).reset_index()
    top_cities = top_cities.sort_values('booked', ascending=False).head(5).to_dict(orient='records')
    # features
    feats = FeatureImportance.objects.all().order_by('-importance')[:10]
    feats_list = [{'feature': f.feature, 'importance': f.importance} for f in feats]
    content = f"""
    AI Summary Report — {datetime.utcnow().date()}
    Total enquiries: {n}
    Booked rate: {booked_rate:.2%}

    Top cities (by bookings):
    {json.dumps(top_cities, indent=2)}

    Top features influencing booking:
    {json.dumps(feats_list, indent=2)}
    """
    report = AIGeneratedReport.objects.create(title=title or f"AI Summary {datetime.utcnow().date()}", content=content, metrics={'n': n, 'booked_rate': booked_rate}, file_path=None)
    return report
