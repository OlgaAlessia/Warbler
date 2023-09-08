"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py

import os
from unittest import TestCase

from models import db, connect_db, User, Message, Likes, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False

class UserViewTestCase(TestCase):
    """Test views for user."""
    
    def setUp(self):
        """Create test user, add sample data."""

        User.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id = 140
        self.testuser.id = self.testuser_id
        
        self.user1 = User.signup( 'olga', 'olga@email.com', 'password', None)
        self.user1id = 160
        self.user1.id = self.user1id
        
        self.user2 = User.signup( 'katie', 'katie@email.com', 'password', None)
        self.user2id = 180
        self.user2.id = self.user2id
        
        self.user3 = User.signup( 'willy', 'willy@email.com', 'password', None)
        self.user4 = User.signup( 'marco', 'marco@email.com', 'password', None)

        db.session.commit()
    
    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()

    def test_users_index(self):
        with self.client as c:
            resp = c.get("/users")

            self.assertIn("@testuser", str(resp.data))
            self.assertIn("@olga", str(resp.data))
            self.assertIn("@katie", str(resp.data))
            self.assertIn("@willy", str(resp.data))
            self.assertIn("@marco", str(resp.data))


    def test_users_search(self):
        with self.client as c:
            resp = c.get("/users?q=o")

            self.assertNotIn("@testuser", str(resp.data))
            self.assertIn("@olga", str(resp.data))            
            self.assertNotIn("@katie", str(resp.data))
            self.assertNotIn("@willy", str(resp.data))
            self.assertIn("@marco", str(resp.data))


    def test_user_show(self):
        with self.client as c:
            resp = c.get(f"/users/{self.user1id}")
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@olga", str(resp.data))
            

    def setup_likes(self):
        m1 = Message(text="something about warble", user_id=self.testuser_id)
        m2 = Message(text="Bla bla", user_id=self.testuser_id)
        m3 = Message(id=1234, text="likable warble", user_id=self.user1id)
        db.session.add_all([m1, m2, m3])
        db.session.commit()

    def test_add_like(self):
        self.setup_likes()
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post("/users/add_like/1234", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            
            likes = Likes.query.filter(Likes.message_id==1234).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.testuser_id)


    def test_remove_like(self):
        self.setup_likes()
        
        like1 = Likes(user_id=self.testuser_id, message_id=1234)
        db.session.add(like1)
        db.session.commit()
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post("/users/add_like/1234", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            
            likes = Likes.query.filter(Likes.message_id==1234).all()
            self.assertEqual(len(likes), 0)
        

    def test_unauthenticated_like(self):
        self.setup_likes()
        
        num_likes = Likes.query.count()
        
        with self.client as c:

            resp = c.post("/users/add_like/1234", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            
            self.assertIn("Access unauthorized", str(resp.data))
            self.assertEqual(num_likes, Likes.query.count())


    def setup_followers(self):
        f1 = Follows(user_being_followed_id=self.user1id, user_following_id=self.testuser_id)
        f2 = Follows(user_being_followed_id=self.user2id, user_following_id=self.testuser_id)
        f3 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.user1id)
        f4 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.user4.id)

        db.session.add_all([f1,f2,f3,f4])
        db.session.commit()

#    def test_user_show_with_follows(self):

    def test_show_following(self):
        
        self.setup_followers()
        with self.client as c:
            
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
            
            resp = c.get(f"/users/{self.testuser_id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@olga", str(resp.data))
            self.assertIn("@katie", str(resp.data))
            self.assertNotIn("@willy", str(resp.data))
            self.assertNotIn("@marco", str(resp.data))
    
    
    def test_unauthorized_following_page_access(self):
        
        self.setup_followers()
        with self.client as c:
            
            resp = c.get(f"/users/{self.testuser_id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@olga", str(resp.data))
            self.assertNotIn("@katie", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))
    
    
    def test_show_followers(self):
            
        self.setup_followers()
        with self.client as c:
            
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
            
            resp = c.get(f"/users/{self.testuser_id}/followers")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@olga", str(resp.data))
            self.assertNotIn("@katie", str(resp.data))
            self.assertNotIn("@willy", str(resp.data))
            self.assertIn("@marco", str(resp.data))


    def test_unauthorized_followers_page_access(self):
        
        self.setup_followers()
        with self.client as c:
            
            resp = c.get(f"/users/{self.testuser_id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@olga", str(resp.data))
            self.assertNotIn("@marco", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))