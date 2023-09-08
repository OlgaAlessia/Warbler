"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows

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


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()
        
        user1 = User.signup( 'user1', 'user1@email.com', 'password', None)
        user1id = 40
        user1.id = user1id
        
        user2 = User.signup( 'user2', 'user2@email.com', 'password', None)
        user2id = 80
        user2.id = user2id
        
        db.session.commit()
        
        user1 = db.session.query(User).filter_by(id=user1id).first()
        user2 = db.session.query(User).filter_by(id=user2id).first()
        self.user1 = user1
        self.user2 = user2
                
        self.client = app.test_client()
        
    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res


    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)



######## Follow Test ########## 

    def test_user_follows(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertEqual(len(self.user1.following), 1)
        self.assertEqual(len(self.user2.following), 0)
        self.assertEqual(len(self.user1.followers), 0)
        self.assertEqual(len(self.user2.followers), 1)

        self.assertEqual(self.user1.following[0].id, self.user2.id)
        self.assertEqual(self.user2.followers[0].id, self.user1.id)
        

######## User.is_following ########## 

    def test_is_following(self):
        
        self.user1.following.append(self.user2)
        db.session.commit()
    
        self.assertTrue(self.user1.is_following(self.user2))
        self.assertFalse(self.user2.is_following(self.user1))


######## User.is_followed_by  ########## 

    def test_is_followed_by(self):
        
        self.user1.followers.append(self.user2)
        db.session.commit()
        
        self.assertTrue(self.user1.is_followed_by(self.user2))
        self.assertFalse(self.user2.is_followed_by(self.user1))
        
    
######## User.signup ##########    
    
    def test_valid_signup(self):
        userTest = User.signup('userTest', 'user1mail@email.com', 'password', None)
        userTestid = 100
        userTest.id = userTestid
               
        userTest = db.session.query(User).filter_by(id=userTestid).first()
        db.session.commit()
        
        self.assertIsNotNone(userTest)
        self.assertEqual(userTest.username, 'userTest')
        self.assertEqual(userTest.email, 'user1mail@email.com')
        self.assertNotEqual(userTest.password, 'password')
        self.assertTrue(userTest.password.startswith("$2b$12$"))
         
    def test_invalid_username_signup(self):
        with self.assertRaises(exc.IntegrityError) as cm:
            invalidUser = User.signup( None, 'invalidUser@email.com', 'password', None)
            invalidUserid = 666
            invalidUser.id = invalidUserid
            db.session.commit()
    
    def test_invalid_email_signup(self):
        with self.assertRaises(exc.IntegrityError) as cm:
            User.signup( 'invalidUser', None, 'password', None)
            db.session.commit()
            
    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError) as cm:
            User.signup( 'invalidUser', 'invalidUser@email.com', None, None)
        
        with self.assertRaises(ValueError) as cm:
            User.signup( 'invalidUser', 'invalidUser@email.com', '', None) 
            self.assertEqual("Password must be non-empty.", str(cm.exception))
        
        
######## User.authenticate ##########
         
    def test_valid_authentication(self):     
        user = User.authenticate(self.user1.username, 'password')
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.user1.id)
            
    def test_invalid_username(self):
        self.assertFalse(User.authenticate("wrongusername", "password")) 
        
    def test_invalid_password(self):
        self.assertFalse(User.authenticate(self.user1.username, "wrongpassword"))    