REJECTION_LABELS = {
    "wrong_category": "Другая категория",
    "wrong_city": "Другой город",
    "wrong_event_format": "Не подходит формат мероприятия",
    "busy": "Занят на выбранную дату",
    "over_budget": "Превышает бюджет",
    "duration_too_long": "Не подходит по длительности",
    "wrong_language": "Не подходит язык",
}


def format_money(value):
    return f"{value:,}".replace(",", " ")


def build_explanation(contractor, request):
    reasons = [
        f"Свободен {request.date.strftime('%d.%m.%Y')}",
        f"Работает в городе {contractor['city']}",
        f"Подходит для формата «{request.event_format}»",
    ]

    if contractor["price"] is not None:
        reserve = (
            request.budget
            - contractor["price"]
        )

        reasons.append(
            f"Цена от {format_money(contractor['price'])} ₸ "
            f"укладывается в бюджет {format_money(request.budget)} ₸; "
            f"запас {format_money(reserve)} ₸"
        )

    if (
        request.duration_hours is not None
        and contractor["max_hours"] is not None
    ):
        reserve = (
            contractor["max_hours"]
            - request.duration_hours
        )

        reasons.append(
            f"Может работать до {contractor['max_hours']:g} ч. "
            f"при необходимых {request.duration_hours:g} ч.; "
            f"запас {reserve:g} ч."
        )

    if request.language:
        reasons.append(
            f"Поддерживает язык «{request.language}»"
        )

    if contractor["price_imputed"]:
        reasons.append(
            "Цена была дополнена при подготовке датасета"
        )

    if contractor["city_imputed"]:
        reasons.append(
            "Город был дополнен при подготовке датасета"
        )

    if contractor["synthetic"]:
        reasons.append(
            "Профиль является синтетической записью датасета"
        )

    return reasons
