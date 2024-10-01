from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from bson import ObjectId
from typing import List
import logging

app = FastAPI()

#Connecting to mongodb bookstore database 
client = AsyncIOMotorClient('mongodb://mongo:27017')
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

# GET /books : Récupérer tous les livres
@app.get("/books", response_model=List[Book])
async def get_books():
    books = await collection.find().to_list(100)
    return [book_helper(book) for book in books]

# GET /books/{book_id} : Récupérer un livre par ID
@app.get("/books/{book_id}", response_model=Book)
async def get_book(book_id: str):
    book = await collection.find_one({"_id": ObjectId(book_id)})
    if book is None:
        raise HTTPException(status_code=404, detail="Livre non trouvé")
    return book_helper(book)

@app.post("/books", response_model=dict)
async def create_book(book: Book):
    try:
        print(book)
        book_data = {
            "title": book.title,
            "author": book.author,
            "summary": book.summary,
        }
        print(book_data)

        # Attempt to insert the book data into the collection
        result = await collection.insert_one(book_data)

        #Fetch the newly created book from the database
        new_book = await collection.find_one({"_id": result.inserted_id})
        
        if new_book is None:
            raise HTTPException(status_code=500, detail="Failed to create book")
        
        return book_data

    except Exception as e:
        logging.error(f"Error creating book: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# PUT /books/{book_id} : Mettre à jour un livre existant
@app.put("/books/{book_id}", response_model=dict)
async def update_book(book_id: str, book: Book):
    # Create a dictionary manually from the Pydantic model
    book_data = {
        "title": book.title,
        "author": book.author,
        "summary": book.summary,
    }
    
    try:
        # Attempt to update the book in the collection
        updated_book = await collection.find_one_and_update(
            {"_id": ObjectId(book_id)},
            {"$set": book_data},
            return_document=True
        )
        
        # Check if the book was found and updated
        if updated_book is None:
            raise HTTPException(status_code=404, detail="Book not found")
        
        return book_helper(updated_book)

    except Exception as e:
        # Log the error and raise a server error
        logging.error(f"Error updating book: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# DELETE /books/{book_id} : Supprimer un livre
@app.delete("/books/{book_id}")
async def delete_book(book_id: str):
    delete_result = await collection.delete_one({"_id": ObjectId(book_id)})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Livre non trouvé")
    return {"message": "Livre supprimé"}
