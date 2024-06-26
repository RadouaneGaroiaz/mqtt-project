from transformers import AutoImageProcessor, AutoModelForImageClassification

def load_model():
    processor = AutoImageProcessor.from_pretrained("gianlab/swin-tiny-patch4-window7-224-finetuned-plantdisease")
    model = AutoModelForImageClassification.from_pretrained("gianlab/swin-tiny-patch4-window7-224-finetuned-plantdisease")