import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
from modules.video.video_generation import VideoGenerator  # Assuming this is the correct import

class TestVideoGenerator(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_path = os.path.join(self.temp_dir.name, "test_output.mp4")
        self.video_generator = VideoGenerator(output_path=self.output_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch('moviepy.editor.ImageClip')
    @patch('moviepy.editor.AudioFileClip')
    @patch('moviepy.editor.concatenate_videoclips')
    def test_create_video_with_audio(self, mock_concat, mock_audio, mock_image):
        mock_image_clip = MagicMock()
        mock_audio_clip = MagicMock()
        mock_final_clip = MagicMock()
        mock_concat.return_value = mock_final_clip
        mock_image.return_value = mock_image_clip
        mock_audio.return_value = mock_audio_clip

        image_paths = ["path/to/image1.jpg", "path/to/image2.jpg"]
        audio_path = "path/to/audio.mp3"
        self.video_generator.create_video_with_audio(image_paths, audio_path)
        mock_image.assert_called()
        mock_audio.assert_called()
        mock_concat.assert_called_once()

    @patch('moviepy.editor.ImageClip')
    @patch('moviepy.editor.concatenate_videoclips')
    def test_create_video_without_audio(self, mock_concat, mock_image):
      
        mock_image_clip = MagicMock()
        mock_final_clip = MagicMock()
        mock_concat.return_value = mock_final_clip
        mock_image.return_value = mock_image_clip

        image_paths = ["path/to/image1.jpg", "path/to/image2.jpg"]

        self.video_generator.create_video_without_audio(image_paths)
        mock_image.assert_called()
        mock_concat.assert_called_once()

    @patch('moviepy.editor.ImageSequenceClip')
    def test_create_video_from_images(self, mock_image_seq_clip):
        mock_image_clip = MagicMock()
        mock_image_seq_clip.return_value = mock_image_clip
        image_paths = ["path/to/image1.jpg", "path/to/image2.jpg"]
        self.video_generator.create_video_from_images(image_paths)

        mock_image_seq_clip.assert_called_once()
        mock_image_clip.write_videofile.assert_called_once_with(self.output_path, fps=24)

if __name__ == '__main__':
    unittest.main()