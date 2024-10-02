from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from bson import ObjectId
from typing import List
import logging

app = FastAPI()

#Connecting to mongodb bookstore database 
client = AsyncIOMotorClient('mongodb://localhost:27018')
db = client['bookstore']
collection = db['books']

# model oop of book 
class Book(BaseModel):
    title: str
    author: str
    summary: str

# converting book instance to dict 
def book_helper(book) -> dict:
    return {
        "id": str(book["_id"]),
        "title": book["title"],
        "author": book["author"],
        "summary": book["summary"]
    }

# GET /books : get all books
@app.get("/books", response_model=List[Book])
async def get_books():
    books = await collection.find().to_list(100)
    return [book_helper(book) for book in books]

# GET /books/{book_id} : get book by id 
@app.get("/books/{book_id}", response_model=Book)
async def get_book(book_id: str):
    book = await collection.find_one({"_id": ObjectId(book_id)})
    if book is None:
        raise HTTPException(status_code=404, detail="Livre non trouvé")
    return book_helper(book)

# POST create a new book and return the id of the book is being returned 
@app.post("/books", response_model=dict)
async def create_book(book: Book):
    try:
        book_data = {
            "title": book.title,
            "author": book.author,
            "summary": book.summary,
        }
        
        result = await collection.insert_one(book_data)
        new_book = await collection.find_one({"_id": ObjectId(result.inserted_id)})
        
        if new_book is None:
            raise HTTPException(status_code=500, detail="Failed to create book")
        
        return book_data

    except Exception as e:
        logging.error(f"Error creating book: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# PUT /books/{book_id} : update an already existing book 
@app.put("/books/{book_id}", response_model=dict)
async def update_book(book_id: str, book: Book):

    book_data = {
        "title": book.title,
        "author": book.author,
        "summary": book.summary,
    }
    
    try:

        updated_book = await collection.find_one_and_update(
            {"_id": ObjectId(book_id)},
            {"$set": book_data},
            return_document=True
        )
        
        if updated_book is None:
            raise HTTPException(status_code=404, detail="Book not found")
        
        return book_helper(updated_book)

    except Exception as e:
        logging.error(f"Error updating book: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# DELETE /books/{book_id} : delete a book by ID 
@app.delete("/books/{book_id}")
async def delete_book(book_id: str):
    delete_result = await collection.delete_one({"_id": ObjectId(book_id)})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="book not found")
    return {"message": "Book Has beeing deleted! "}
