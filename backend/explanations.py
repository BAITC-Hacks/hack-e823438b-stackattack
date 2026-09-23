"""Explanations use structured facts only."""

REJECTION_LABELS = {
    "wrong_category": "Не подходит категория",
    "wrong_city": "Не подходит город",
    "wrong_event_format": "Не подходит формат мероприятия",
    "busy": "Дата указана среди занятых",
    "price_unknown": "Стартовая цена не указана",
    "over_budget": "Стартовая цена выше бюджета",
    "duration_unknown": "Максимальная длительность не указана",
    "duration_exceeded": "Превышена максимальная длительность",
    "language_mismatch": "Нужный язык не указан",
    "below_top_3": "Прошёл фильтры, но находится ниже TOP-3",
}


def build_explanation(contractor, request):
    facts = [
        ("city", contractor.city, request.city, f"Город: {contractor.city}"),
        ("category", contractor.categories, request.category, f"Категория: {request.category}"),
        ("event_format", contractor.event_formats, request.event_format, f"Поддерживает формат «{request.event_format}»"),
        ("availability", contractor.busy_dates, request.date, f"Дата {request.date} не указана среди занятых; доступность требует подтверждения"),
        ("budget", contractor.price_from_kzt, request.budget, f"Цена от {contractor.price_from_kzt} ₸ при бюджете {request.budget} ₸"),
        ("budget_headroom", request.budget - contractor.price_from_kzt, None, f"Запас относительно стартовой цены: {request.budget - contractor.price_from_kzt} ₸"),
    ]
    if request.duration_hours is not None:
        facts.append(("duration", contractor.max_hours, request.duration_hours, f"До {contractor.max_hours} ч при необходимых {request.duration_hours} ч"))
    if request.language is not None:
        facts.append(("language", contractor.languages, request.language, f"Указан язык: {request.language}"))
    return [dict(code=code, actual=actual, requested=requested, text=text) for code, actual, requested, text in facts]


def rejection_details(contractor, request, stage, code):
    actual = {
        "category": contractor.categories, "city": contractor.city,
        "event_format": contractor.event_formats, "availability": contractor.busy_dates,
        "budget": contractor.price_from_kzt, "duration": contractor.max_hours,
        "language": contractor.languages,
    }[stage]
    requested = getattr(request, {"availability": "date", "duration": "duration_hours"}.get(stage, stage))
    return dict(contractor_id=contractor.id, name=contractor.anon_name, rejected_at=stage,
                reason=code, details=REJECTION_LABELS[code], actual=actual, requested=requested)
