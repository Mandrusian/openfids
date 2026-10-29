"""North Queensland Airports (NQA) feed adapter for OpenFIDS."""

FEED_URL = "https://flights.nqa.au/v1/flights"


def convert_flight(raw):
    """Translate an NQA flight to OpenFIDS's standard board fields."""
    if not isinstance(raw, dict):
        return None
    direction = str(raw.get("direction") or "").upper()
    if direction not in ("A", "D") or not raw.get("scheduled"):
        return None
    airport = str(raw.get("airport") or "").upper()
    port = raw.get("port") if isinstance(raw.get("port"), dict) else {}
    aircraft = raw.get("aircraft") if isinstance(raw.get("aircraft"), dict) else {}
    status = raw.get("status") if isinstance(raw.get("status"), dict) else {}
    airline = str(raw.get("airline") or "").upper()
    number = str(raw.get("flightNumber") or "")
    full_number = str(raw.get("flight") or "")
    if not number and airline and full_number.upper().startswith(airline):
        number = full_number[len(airline):]
    return {
        "id": f"NQA-{airport}-{raw.get('id') or (direction + '-' + full_number + '-' + str(raw['scheduled']))}",
        "airport": airport,
        "public": raw.get("public"),
        "vector": direction,
        "airline": airline,
        "flightNumber": number,
        "portIATA": port.get("iata") or "",
        "portName": port.get("name") or "",
        "terminal": raw.get("terminal") or "",
        "scheduled": raw["scheduled"],
        "estimated": raw.get("estimated"),
        "actual": raw.get("actual"),
        "onBlock": raw.get("onBlock"),
        "offBlock": raw.get("offBlock"),
        "statusMsgPublic": status.get("public") or "",
        "gate": raw.get("gate") or "",
        "stand": raw.get("stand") or "",
        "carousel": raw.get("carousel") or "",
        "acType": aircraft.get("type") or "",
        "acRego": aircraft.get("registration") or "",
        "codeShares": raw.get("codeShares") if isinstance(raw.get("codeShares"), list) else [],
        "flightType": raw.get("flightType") or "",
    }


def extract_flights(data, airport="CNS", include_non_public=True):
    """Extract (flights, metadata) for CNS, MKY, or ALL."""
    if not isinstance(data, dict) or not isinstance(data.get("flights"), list):
        raise ValueError("NQA response must contain a flights array")
    airport = str(airport or "CNS").upper()
    if airport not in ("CNS", "MKY", "ALL"):
        raise ValueError("airport must be CNS, MKY or ALL")
    flights = []
    for raw in data["flights"]:
        if not isinstance(raw, dict):
            continue
        if airport != "ALL" and str(raw.get("airport") or "").upper() != airport:
            continue
        if not include_non_public and str(raw.get("public") or "").upper() == "N":
            continue
        item = convert_flight(raw)
        if item is not None:
            flights.append(item)
    metadata = {
        "sourceTimestamp": data.get("sourceTimestamp"),
        "receivedAt": data.get("receivedAt"),
        "generatedAt": data.get("generatedAt"),
        "ageSeconds": data.get("ageSeconds"),
        "sourceAgeSeconds": data.get("sourceAgeSeconds"),
        "stale": bool(data.get("stale", False)),
        "staleReasons": data.get("staleReasons") if isinstance(data.get("staleReasons"), list) else [],
        "count": len(flights),
    }
    return flights, metadata
