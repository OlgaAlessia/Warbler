"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py

import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

class MessageModelTestCase(TestCase):
    """Test model for messages."""
    
    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()
            
        user = User.signup( 'userTest', 'userTest@email.com', 'password', None)
        userid = 44
        user.id = userid
        
        db.session.commit()
        
        user = db.session.query(User).filter_by(id=userid).first()
        self.user = user
                
        self.client = app.test_client()
    
    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res
    
    
    def test_message_model(self):
        """Does basic model work?"""

        msg = Message(text='Prova Text')
        self.user.messages.append(msg)
        
        db.session.commit()
        
        # User should have 1 messages
        self.assertEqual(len(self.user.messages), 1)
        self.assertEqual(self.user.messages[0].text, "Prova Text")
        
        
    def test_message_likes(self):
        
        msg1 = Message(text="Message Prova Text 1", user_id=self.user.id)
        msg2 = Message(text="Message Prova Text 2", user_id=self.user.id)
        db.session.add_all([msg1, msg2])
        
        reader = User.signup( 'reader', 'reader@email.com', 'password', None)
        readerid = 46
        reader.id = readerid
        db.session.commit()
        
        self.assertEqual(len(reader.likes), 0)
        
        msg_like = Likes(user_id=readerid, message_id=msg1.id)
        db.session.add(msg_like)
        db.session.commit()
        
        
        list_like = db.session.query(Likes).filter(Likes.user_id == readerid).all()
        self.assertEqual(len(list_like), 1)
        self.assertEqual(list_like[0].message_id, msg_like.id)
        
        
        # The user press like again which means delete the message from likes
        msg = db.session.query(Likes).filter(Likes.user_id == readerid, Likes.message_id == msg_like.id).one()
        db.session.delete(msg)
        db.session.commit()
        
        self.assertEqual(len(reader.likes), 0)