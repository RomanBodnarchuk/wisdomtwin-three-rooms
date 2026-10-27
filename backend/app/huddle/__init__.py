"""Audio Executive Huddle Orchestrator & Vendor-Agnostic Voice Abstraction Layer."""

from .voice_interface import (
    AzureSpeechVoiceAdapter,
    DessaVoiceAdapterStub,
    GrokRealtimeVoiceAdapter,
    OpenAIRealtimeVoiceAdapter,
    VoiceAbstractionLayer,
    VoiceSessionHandle,
    get_voice_adapter,
)
from .orchestrator import AudioHuddleOrchestrator

__all__ = [
    "AudioHuddleOrchestrator",
    "AzureSpeechVoiceAdapter",
    "DessaVoiceAdapterStub",
    "GrokRealtimeVoiceAdapter",
    "OpenAIRealtimeVoiceAdapter",
    "VoiceAbstractionLayer",
    "VoiceSessionHandle",
    "get_voice_adapter",
]
