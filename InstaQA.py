from flask import Flask, request, jsonify,render_template
from yt_dlp import YoutubeDL
import os,requests,json
import uuid
import whisper

def call_ollama(question, model="llama3"):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": question,
            "stream": False
        }
    )
    result = response.json()
    return result.get("response", "").strip()



app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')


@app.route('/process', methods=['POST'])
def process_reel():
    data = request.get_json()
    reel_url = data.get('url')
    if not reel_url:
        return jsonify({"error": "URL is required"}), 400

    filename = f"downloads/{uuid.uuid4()}"

    # Step 1: Download Instagram Reel audio
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': filename,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }]
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([reel_url])
    except Exception as e:
        return jsonify({"error": f"Download failed: {str(e)}"}), 500

    # Step 2: Transcribe with Whisper
    try:
        model = whisper.load_model("base")
        result = model.transcribe(filename+'.mp3')
    except Exception as e:
        return jsonify({"error": f"Transcription failed: {str(e)}"}), 500
    text = result['text']
    prompt = f'''You are an intelligent assistant. Given a block of text, your job is to:

1. Identify any explicit or implicit **questions** found in the text.
2. Provide a **brief and accurate answer** to each question.
3. Use the text content to answer wherever possible. If the answer is not present, use general knowledge to answer.
4. Return only a **JSON array** of objects, where each object has:
   - "question": the extracted question
   - "answer": your answer to that question

Do not include any additional explanation. Output only valid JSON.

Here is the text:
{text}
 '''

    result = json.loads(call_ollama(prompt))
    print(type(result))
    return jsonify(result)

if __name__ == '__main__':
    os.makedirs("downloads", exist_ok=True)
    app.run(debug=True)

