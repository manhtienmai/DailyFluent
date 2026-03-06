from django.test import TestCase
from django.contrib.auth import get_user_model

from .models import Assignment, Notification

User = get_user_model()


class NotificationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student1", email="student1@test.com", password="testpass123"
        )
        self.teacher = User.objects.create_user(
            username="teacher1",
            email="teacher1@test.com",
            password="testpass123",
            is_staff=True,
        )

    def test_create_notification(self):
        n = Notification.objects.create(
            user=self.user,
            category="study",
            title="Time to review!",
            message="You have pending reviews.",
            link="/vocab/review",
        )
        self.assertFalse(n.is_read)
        self.assertEqual(n.category, "study")
        self.assertEqual(str(n), f"● [study] Time to review! → {self.user}")

    def test_mark_as_read(self):
        n = Notification.objects.create(
            user=self.user, category="system", title="Welcome!"
        )
        n.is_read = True
        n.save()
        self.assertTrue(n.is_read)
        self.assertIn("✓", str(n))

    def test_assignment_creates_notifications(self):
        student2 = User.objects.create_user(
            username="student2", email="student2@test.com", password="testpass123"
        )
        assignment = Assignment.objects.create(
            teacher=self.teacher,
            title="Grammar Quiz",
            description="Complete this quiz by Friday",
            quiz_type="grammar",
            quiz_id="present-simple",
            link="/exam/english/grammar/present-simple",
        )
        assignment.assigned_to.set([self.user, student2])
        count = assignment.create_notifications()

        self.assertEqual(count, 2)
        self.assertEqual(
            Notification.objects.filter(category="assignment").count(), 2
        )
        # Check the student got the notification
        notif = Notification.objects.filter(user=self.user, category="assignment").first()
        self.assertIn("Grammar Quiz", notif.title)
        self.assertEqual(notif.link, "/exam/english/grammar/present-simple")

    def test_unread_count(self):
        Notification.objects.create(user=self.user, title="N1")
        Notification.objects.create(user=self.user, title="N2")
        Notification.objects.create(user=self.user, title="N3", is_read=True)
        self.assertEqual(
            Notification.objects.filter(user=self.user, is_read=False).count(), 2
        )
