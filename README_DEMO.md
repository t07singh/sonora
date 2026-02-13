# 🎌 Sonora Studio: Demo Guide

Welcome to the **Production Asset** phase. To ensure series consistency, you must first digitize your characters.

## 🎙️ Character Digitization (Casting)

Before starting a dubbing run, register your lead voices using the casting utility. This extracts the unique vocal embedding and locks it into the registry.

**Run the following command:**
```bash
python cast_character.py --name SAKURA --source path/to/clean_sample.wav
```

## 🎬 Studio Workflow

1.  **Launch the Hub**: Start the Sonora Studio application.
2.  **Synthesis**: Use the **Studio Hub** tab to synthesize dialogue.
3.  **Asset Lock**: If a take is perfect, click **"Save Take to Registry"** in the UI to update the character's production profile.
4.  **Mixing**: Open the **Mixer Deck** to adjust the stems and final master.

---
*Sonora Studio Hub v5.2.0-PROD*
