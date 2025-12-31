COACH_OUTPUT_SCHEMA = {
    "name": "teenmind_coach_output",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "intent": {
                "type": "string",
                "enum": ["anxiety", "stress", "sadness", "conflict", "sleep", "other"]
            },
            "tone": {
                "type": "string",
                "enum": ["calm", "overwhelmed", "panicky", "angry", "sad", "numb", "confused", "other"]
            },
            "risk_level": {
                "type": "string",
                "enum": ["low", "medium", "high"]
            },
            "should_offer_skill": {"type": "boolean"},
            "assistant_message": {"type": "string"}
        },
        "required": ["intent", "tone", "risk_level", "should_offer_skill", "assistant_message"]
    },
    "strict": True
}