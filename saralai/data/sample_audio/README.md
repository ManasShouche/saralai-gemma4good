# Sample Audio Clips

Test audio for transcription and NLU pipeline validation.

## Files

| File | Language | Transcript | Duration |
|------|----------|-----------|----------|
| `rukmini_kn.webm` | Kannada | "ನನ್ನ ಗಂಡ ಎರಡು ವರ್ಷದ ಹಿಂದೆ ತೀರಿಕೊಂಡರು. ನಮ್ಮ ಬಳಿ ಬಿಪಿಎಲ್ ರೇಷನ್ ಕಾರ್ಡ್ ಇದೆ." | ~8s |
| `rukmini_hi.webm` | Hindi | "मेरे पति दो साल पहले गुज़र गए। हमारे पास BPL राशन कार्ड है।" | ~8s |
| `raju_en.webm` | English | "I am a farmer. I own less than 2 acres of land. I have two children in school." | ~7s |

## Generating fixtures

```bash
# Using Kokoro TTS (same engine as backend fallback)
python -c "
from kokoro import KPipeline
pipe = KPipeline(lang_code='kn')
audio, sr = pipe('ನನ್ನ ಗಂಡ ಎರಡು ವರ್ಷದ ಹಿಂದೆ ತೀರಿಕೊಂಡರು')
import soundfile as sf
sf.write('rukmini_kn.wav', audio, sr)
"
```

## Expected transcription output

```json
{
  "transcript": "My husband passed away two years ago. We have a BPL ration card.",
  "language_detected": "kn",
  "confidence": 0.94,
  "welfare_signals": ["widow", "bpl_ration_card"]
}
```
