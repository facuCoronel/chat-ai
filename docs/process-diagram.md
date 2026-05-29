# Diagrama de Procesos — Mensajería + Insights

```mermaid
flowchart TD
    subgraph INCOMING["Mensaje Entrante — WhatsApp to Sistema"]
        WA_META["Meta / WhatsApp Cloud API"]
        WEBHOOK_POST["POST /api/v1/webhook\nwebhook_router.py"]
        SIG_VAL["Validar firma HMAC-SHA256\nsignature_validator.py"]
        BG_TASK["BackgroundTask\n200 OK inmediato a Meta"]
        CTRL["WebhookController\nwebhook_controller.py"]
        PARSER["WhatsAppWebhookParser\nwhatsapp_parser.py"]

        WA_META -->|"payload + firma"| WEBHOOK_POST
        WEBHOOK_POST --> SIG_VAL
        SIG_VAL -->|"valida"| BG_TASK
        BG_TASK --> CTRL
        CTRL --> PARSER
    end

    subgraph RECEIVE["ReceiveMessageUseCase — receive_message.py"]
        RECEIVE_UC["execute()"]
        DEDUP{"Existe wamid?"}
        END_DUP["skip — duplicado"]
        CONV_BUILD["build_conversation_data()\nnormalizacion + conversation_id"]
        ENTITY["IncomingMessage entity\nsender_role = BUYER"]
        SAVE_MSG["MessageRepository.save()"]
        WS_PUB["WebSocket publish"]

        RECEIVE_UC --> DEDUP
        DEDUP -->|"ya existe"| END_DUP
        DEDUP -->|"no existe"| CONV_BUILD
        CONV_BUILD --> ENTITY
        ENTITY --> SAVE_MSG
        SAVE_MSG --> WS_PUB
    end

    subgraph OUTGOING["Mensaje Saliente — Sistema to WhatsApp"]
        FRONTEND["Frontend / API Client"]
        REPLY_EP["POST /api/v1/messages/reply\nreply_router.py"]
        REPLY_UC["ReplyMessageUseCase\nreply_message.py"]
        WA_CLIENT["HttpxWhatsAppClient\nMeta Graph API v20.0"]
        SAVE_SELLER["Guardar sender_role = SELLER\nMessageRepository.save()"]
        WS_PUB2["WebSocket publish"]

        FRONTEND --> REPLY_EP
        REPLY_EP --> REPLY_UC
        REPLY_UC --> WA_CLIENT
        WA_CLIENT -->|"wamid de Meta"| REPLY_UC
        REPLY_UC --> SAVE_SELLER
        SAVE_SELLER --> WS_PUB2
    end

    subgraph INSIGHT["GenerateInsightUseCase — generate_insight.py"]
        INSIGHT_ENTRY["run_insight_safely()\nfire-and-forget — _background.py"]
        TEXT_CHECK{"Tiene raw_text?"}
        END_SKIP["skip — sin texto"]
        TYPE_CHECK{"message_type\n== AUDIO?"}
        DOWNLOAD["FUTURO: Descargar audio\nWhatsApp Media API"]
        TRANSCRIBE["FUTURO: Transcribir\ncon Ollama whisper"]
        CTX_LOAD["Cargar 10 insights recientes\ndel conversation_id"]
        PROMPT_BUILD["Construir prompt\nmensaje + contexto + reglas de negocio"]
        OLLAMA_CALL["HttpxOllamaClient.generate()\nOLLAMA_BASE_URL — format=json"]
        PARSE_RESP["Parsear respuesta JSON\nsentiment, intent, urgency\ncommercial_risk, summary"]
        SAVE_INSIGHT["InsightRepository.save()\nmessage_insights table"]

        INSIGHT_ENTRY --> TEXT_CHECK
        TEXT_CHECK -->|"sin texto"| END_SKIP
        TEXT_CHECK -->|"con texto"| TYPE_CHECK
        TYPE_CHECK -->|"es audio"| DOWNLOAD
        DOWNLOAD --> TRANSCRIBE
        TRANSCRIBE --> CTX_LOAD
        TYPE_CHECK -->|"texto / otro"| CTX_LOAD
        CTX_LOAD --> PROMPT_BUILD
        PROMPT_BUILD --> OLLAMA_CALL
        OLLAMA_CALL --> PARSE_RESP
        PARSE_RESP --> SAVE_INSIGHT
    end

    subgraph DB["Base de Datos — PostgreSQL / SQLite"]
        T_MSG["incoming_messages"]
        T_INSIGHT["message_insights"]
        T_BA["business_accounts"]
    end

    subgraph WS["WebSocket /ws/messages"]
        WS_CLIENTS["Frontend clients — tiempo real"]
    end

    PARSER       -->|"ReceiveMessageRequest DTO"| RECEIVE_UC
    SAVE_MSG     --> INSIGHT_ENTRY
    SAVE_SELLER  --> INSIGHT_ENTRY
    SAVE_MSG     --> T_MSG
    SAVE_SELLER  --> T_MSG
    SAVE_INSIGHT --> T_INSIGHT
    CONV_BUILD   -.->|"lookup"| T_BA
    WS_PUB       --> WS_CLIENTS
    WS_PUB2      --> WS_CLIENTS

    classDef future fill:#fff3cd,stroke:#ffc107,stroke-width:2px,color:#000
    classDef trigger fill:#d4edda,stroke:#28a745,stroke-width:2px
    classDef db fill:#cce5ff,stroke:#004085,stroke-width:2px
    classDef skip fill:#f8d7da,stroke:#721c24,stroke-width:1px,color:#721c24

    class DOWNLOAD,TRANSCRIBE future
    class INSIGHT_ENTRY trigger
    class T_MSG,T_INSIGHT,T_BA db
    class END_DUP,END_SKIP skip
```

---

## Leyenda de colores

| Color | Significado |
|-------|-------------|
| Amarillo | **Funcionalidad futura** — descarga y transcripción de audio con Ollama |
| Verde | Trigger de insight (fire-and-forget) |
| Azul | Tablas de base de datos |
| Rojo | Paths de salida temprana (skip) |

---

## Expansion de Audio — Plan

Cuando ingresa un mensaje de tipo `AUDIO`:

1. **Detectar** `message_type == MessageType.AUDIO` en `GenerateInsightUseCase`
2. **Descargar** el archivo desde Meta con `whatsapp_client.download_media(media_id)`
3. **Transcribir** usando Ollama con `ollama_client.transcribe(audio_bytes, model)`
4. **Continuar** el flujo normal con el texto transcripto

### Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `domain/services/ollama_client.py` | Agregar `transcribe(audio_bytes, model)` |
| `infrastructure/http/ollama_client.py` | Implementar llamada HTTP de transcripcion |
| `application/use_cases/generate_insight.py` | Branch `if message_type == AUDIO` antes de `CTX_LOAD` |
| `infrastructure/http/whatsapp_client.py` | Agregar `download_media(media_id)` |
| `domain/services/whatsapp_client.py` | Interfaz `download_media` |
