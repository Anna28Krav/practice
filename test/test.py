import pytest
import sqlite3
from bot import connect_to_db, add_user, get_favorites

def test_connect_to_db():
    connection = connect_to_db()
    assert isinstance(connection, sqlite3.Connection)
    connection.close()

def test_add_user():
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute('DELETE FROM Users WHERE Id = 12345')
    connection.commit()
    connection.close()

    add_user(12345)

    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Users WHERE Id = 12345')
    user = cursor.fetchone()
    assert user is not None
    connection.close()

def test_get_favorites():
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute('DELETE FROM Favorites WHERE UserId = 12345')
    cursor.execute('INSERT INTO Favorites (UserId, Link) VALUES (?, ?)', (12345, 'https://example.com'))
    connection.commit()
    connection.close()

    favorites = get_favorites(12345)
    assert 'https://example.com' in favorites
