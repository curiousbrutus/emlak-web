import unittest
from unittest.mock import patch, MagicMock
import asyncio

from utils.background_tasks import BackgroundTaskManager, TaskWrapper


class TestBackgroundTaskManager(unittest.TestCase):

    def setUp(self):
        self.manager = BackgroundTaskManager()

    def tearDown(self):
        self.manager.shutdown()

    def test_start_task(self):
        async def mock_task():
            pass

        task = self.manager.start_task(mock_task())
        self.assertIsInstance(task, TaskWrapper)
        self.assertIn(task.task, self.manager.tasks)

    def test_start_task_with_callback(self):
        async def mock_task():
            return "Task Result"

        mock_callback = MagicMock()
        task = self.manager.start_task(mock_task(), callback=mock_callback)
        asyncio.run(task.task)
        mock_callback.assert_called_once_with("Task Result")

    def test_start_task_with_exception(self):
        async def mock_task():
            raise ValueError("Task Failed")

        mock_callback = MagicMock()
        task = self.manager.start_task(mock_task(), callback=mock_callback)
        asyncio.run(task.task)
        mock_callback.assert_called_once()
        self.assertIsInstance(mock_callback.call_args[0][0], ValueError)

    def test_cancel_task(self):
        async def mock_task():
            await asyncio.sleep(1)

        task = self.manager.start_task(mock_task())
        self.assertTrue(self.manager.cancel_task(task.id))
        self.assertFalse(self.manager.cancel_task(task.id))

    def test_cancel_nonexistent_task(self):
        self.assertFalse(self.manager.cancel_task("nonexistent_id"))

    def test_cancel_all_tasks(self):
        async def mock_task():
            await asyncio.sleep(1)

        task1 = self.manager.start_task(mock_task())
        task2 = self.manager.start_task(mock_task())
        self.assertTrue(self.manager.cancel_all_tasks())
        self.assertFalse(self.manager.cancel_all_tasks())
        self.assertNotIn(task1.task, self.manager.tasks)
        self.assertNotIn(task2.task, self.manager.tasks)

    def test_shutdown(self):
        async def mock_task():
            await asyncio.sleep(1)

        self.manager.start_task(mock_task())
        self.manager.shutdown()
        self.assertEqual(len(self.manager.tasks), 0)


class TestTaskWrapper(unittest.TestCase):

    def test_task_wrapper_attributes(self):
        mock_task = MagicMock()
        wrapper = TaskWrapper("test_id", mock_task)
        self.assertEqual(wrapper.id, "test_id")
        self.assertEqual(wrapper.task, mock_task)


if __name__ == "__main__":
    unittest.main()