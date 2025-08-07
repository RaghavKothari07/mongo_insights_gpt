from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
from pymongo import MongoClient
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

client = MongoClient("mongodb://localhost:27017")  # or MongoDB Atlas URL
db = client["sample_db"]
collection = db["sample_collection"]

app = FastAPI()

class NLQuery(BaseModel):
    question: str

SYSTEM_PROMPT = """
You are a MongoDB expert. Your task is to convert a user's question into a valid MongoDB .find() query.
Only return the query as Python code in JSON syntax, no explanation.
"""

@app.post("/query")
def query_mongodb(nl: NLQuery):
    try:
        prompt = SYSTEM_PROMPT + f"\nUser question: {nl.question}\nMongo query:"
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": nl.question}
            ],
            temperature=0.2
        )
        raw_query = response["choices"][0]["message"]["content"]
        query_dict = eval(raw_query.strip())

        result_cursor = collection.find(query_dict).limit(10)
        results = [doc for doc in result_cursor]
        for r in results:
            r.pop("_id", None)

        return {"query": query_dict, "results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
