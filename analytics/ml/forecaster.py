"""
Expense Forecaster using Facebook Prophet + moving-average fallback.
Predicts future spending for the next N days.
Heavy imports (pandas, prophet) are deferred to function-call time.
"""
from datetime import date, timedelta


def forecast_expenses(user, days_ahead: int = 30) -> dict:
    """
    Forecast user expenses for the next `days_ahead` days.
    Returns a dict with dates and predicted amounts.
    """
    from transactions.models import Transaction
    from django.db.models import Sum
    from django.db.models.functions import TruncDate
    import pandas as pd

    # Aggregate daily expenses
    qs = (
        Transaction.objects
        .filter(user=user, transaction_type='expense')
        .annotate(day=TruncDate('date'))
        .values('day')
        .annotate(total=Sum('amount'))
        .order_by('day')
    )

    if qs.count() < 14:
        return _simple_moving_average_forecast(qs, days_ahead)

    df = pd.DataFrame(list(qs))
    df.rename(columns={'day': 'ds', 'total': 'y'}, inplace=True)
    df['ds'] = pd.to_datetime(df['ds'])
    df['y'] = df['y'].astype(float)

    try:
        from prophet import Prophet
        model = Prophet(yearly_seasonality=False, weekly_seasonality=True,
                        daily_seasonality=False, interval_width=0.80)
        model.fit(df)
        future = model.make_future_dataframe(periods=days_ahead)
        forecast = model.predict(future)
        result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(days_ahead)
        return {
            'dates': result['ds'].dt.strftime('%Y-%m-%d').tolist(),
            'predicted': [max(0, round(v, 2)) for v in result['yhat'].tolist()],
            'lower': [max(0, round(v, 2)) for v in result['yhat_lower'].tolist()],
            'upper': [max(0, round(v, 2)) for v in result['yhat_upper'].tolist()],
            'method': 'prophet',
        }
    except Exception:
        return _simple_moving_average_forecast(qs, days_ahead)


def _simple_moving_average_forecast(qs, days_ahead: int) -> dict:
    """Fallback: 7-day moving average forecast."""
    if not qs:
        avg = 0
    else:
        totals = [float(r['total']) for r in qs]
        avg = sum(totals[-7:]) / max(len(totals[-7:]), 1)

    today = date.today()
    dates = [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, days_ahead + 1)]
    predicted = [round(avg, 2)] * days_ahead
    return {
        'dates': dates,
        'predicted': predicted,
        'lower': [round(avg * 0.7, 2)] * days_ahead,
        'upper': [round(avg * 1.3, 2)] * days_ahead,
        'method': 'moving_average',
    }


def get_monthly_trend(user, months: int = 6) -> dict:
    """Returns month-wise income and expense for the last N months."""
    from transactions.models import Transaction
    from django.db.models import Sum
    from django.db.models.functions import TruncMonth
    qs = (
        Transaction.objects
        .filter(user=user)
        .annotate(month=TruncMonth('date'))
        .values('month', 'transaction_type')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    data = {}
    for row in qs:
        m = row['month'].strftime('%b %Y')
        if m not in data:
            data[m] = {'income': 0, 'expense': 0}
        data[m][row['transaction_type']] = float(row['total'])

    labels = list(data.keys())[-months:]
    incomes = [data[m].get('income', 0) for m in labels]
    expenses = [data[m].get('expense', 0) for m in labels]
    return {'labels': labels, 'incomes': incomes, 'expenses': expenses}
