import re
import warnings

import pyttsx3
import requests
import sounddevice as sd
import whisper

warnings.filterwarnings("ignore", category=UserWarning)

CORTEX_URL = "http://localhost:8001/cortex/chat"


class VoiceGateway:
    def __init__(self):
        # 1. Configura Voz (TTS)
        self.tts_engine = pyttsx3.init()
        self._setup_voice()

        # 2. Carrega Whisper
        print("⏳ Carregando motor de IA de reconhecimento de voz...")
        # MUDANÇA: 'small' entende português MUITO melhor que o 'base'
        self.whisper_model = whisper.load_model("small")

    def _setup_voice(self):
        voices = self.tts_engine.getProperty("voices")
        for voice in voices:
            if "Brazil" in voice.name or "PT-BR" in voice.id.upper():
                self.tts_engine.setProperty("voice", voice.id)
                break
        self.tts_engine.setProperty("rate", 170)

    def speak(self, text: str):
        print(f"\n🔊 NEXUS: {text}")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def listen(self, duration=6) -> str:
        """Grava áudio do microfone e transcreve direto da memória (Alta Qualidade)."""
        fs = 16000  # Taxa de amostragem padrão do Whisper
        print(f"\n🎙️ Ouvindo... (Você tem {duration} segundos para falar)")

        # MUDANÇA: Gravando direto em float32 (o formato nativo do Whisper)
        recording = sd.rec(
            int(duration * fs), samplerate=fs, channels=1, dtype="float32"
        )
        sd.wait()

        # MUDANÇA: Transforma a matriz bidimensional em um array linear simples (1D)
        audio_array = recording.flatten()

        print("⏳ Transcrevendo (Whisper)...")
        # MUDANÇA: Passando o array direto, sem criar arquivo .wav temporário
        result = self.whisper_model.transcribe(audio_array, language="pt", fp16=False)

        text = result["text"].strip()
        print(f"🗣️ Você: {text}")
        return text

    def run(self):
        self.speak("Gateway de voz iniciado. Diga Nexus seguido do seu comando.")

        while True:
            # Ouve continuamente em janelas curtas
            user_text = self.listen(duration=5)

            # 1. Filtro de Ruído: ignora transcrições muito curtas ou murmúrios
            if len(user_text) < 4:
                continue

            texto_minusculo = user_text.lower()

            # 2. Comandos de encerramento do sistema
            if texto_minusculo.replace(".", "") in [
                "encerrar nexus",
                "desligar voz",
                "sair",
            ]:
                self.speak("A encerrar a interface de voz. Até logo.")
                break

            # 3. WAKE WORD (A Magia acontece aqui)
            if "nexus" not in texto_minusculo:
                # Ouve, transcreve, mas se não disser "Nexus", o sistema fica em silêncio absoluto.
                continue

            # 4. Limpeza: Remove a palavra "nexus" da frase antes de enviar à inteligência
            comando_limpo = re.sub(r"(?i)nexus[.,!?:;]*\s*", "", user_text).strip()

            # Se o utilizador apenas disse "Nexus" e mais nada, ignoramos ou pedimos a continuação
            if not comando_limpo:
                self.speak("Estou a ouvir.")
                continue

            # 5. Fluxo normal: Envia o comando limpo para o Córtex
            try:
                print(f"🧠 Córtex a processar o comando: '{comando_limpo}'...")
                response = requests.post(CORTEX_URL, json={"message": comando_limpo})

                if response.status_code == 200:
                    data = response.json()
                    reply = data.get("reply", "Erro ao formatar resposta.")

                    if data.get("report"):
                        print(f"⚙️ Ações: {data['report']}")

                    self.speak(reply)
                else:
                    self.speak("O Córtex retornou um erro de processamento.")

            except requests.exceptions.ConnectionError:
                self.speak("Não consegui ligar-me ao servidor do Córtex.")


if __name__ == "__main__":
    gateway = VoiceGateway()
    gateway.run()
