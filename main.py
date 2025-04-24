from fastapi import FastAPI
from pydantic import BaseModel
from youtube_utils import get_video_data
from embedding_utils import store_transcript, answer_question
import uvicorn
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
  video_url: str


class QuestionRequest(BaseModel):
  question: str
  doc_id: str


@app.get("/")
def home():
  return {"message": "YouTube-QnA Backend is running"}


@app.post("/process/")
async def process_video(data: VideoRequest):
  video_url = data.video_url
  title, transcript = get_video_data(video_url)
  doc_id = store_transcript(title, transcript)
  return {
      "message": "Video processed successfully",
      "doc_id": doc_id,
      "title": title
  }


@app.post("/ask/")
async def ask_question(data: QuestionRequest):
  query = data.question
  doc_id = data.doc_id
  answer = answer_question(query, doc_id)
  return {"answer": answer}


if __name__ == "__main__":
  uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
