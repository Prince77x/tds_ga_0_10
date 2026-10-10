import csv
import re
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


CSV_FILE = Path(__file__).parent / "q-fastapi.csv"
students = []


positive_words = {
    "love", "loved", "like", "liked", "excellent", "amazing",
    "awesome", "great", "good", "wonderful", "fantastic",
    "happy", "joy", "delighted", "pleased", "best", "success",
    "successful", "enjoy", "enjoyed", "helpful", "perfect",
    "beautiful", "brilliant", "thank", "thanks", "congratulations",
    "congrats", "win", "won", "excited", "improve", "improved",
}

negative_words = {
    "hate", "hated", "terrible", "awful", "bad", "horrible",
    "sad", "angry", "mad", "worst", "poor", "fail", "failed",
    "failure", "problem", "problems", "error", "errors", "wrong",
    "broken", "damage", "damaged", "disappointed", "disappointing",
    "frustrated", "frustrating", "annoyed", "annoying", "fear",
    "afraid", "worry", "worried", "regret", "pain", "painful",
    "lose", "lost", "cancel", "cancelled", "reject", "rejected",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global students

    with CSV_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        students = [
            {
                "studentId": int(row["studentId"]),
                "class": row["class"],
            }
            for row in reader
        ]

    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api")
def get_students(
    classes: list[str] | None = Query(default=None, alias="class")
):
    if classes is None:
        result = students
    else:
        requested_classes = set(classes)
        result = [
            student
            for student in students
            if student["class"] in requested_classes
        ]

    return {"students": result}


class SentimentRequest(BaseModel):
    sentences: list[str]


def classify_sentiment(sentence: str) -> str:
    words = set(re.findall(r"[a-z']+", sentence.lower()))

    positive_score = len(words & positive_words)
    negative_score = len(words & negative_words)

    if positive_score > negative_score:
        return "happy"

    if negative_score > positive_score:
        return "sad"

    return "neutral"


@app.post("/sentiment")
def analyze_sentiment(request: SentimentRequest):
    return {
        "results": [
            {
                "sentence": sentence,
                "sentiment": classify_sentiment(sentence),
            }
            for sentence in request.sentences
        ]
    }