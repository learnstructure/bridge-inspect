import segmentation_models_pytorch as smp


def get_model():
    model = smp.Unet(
        encoder_name="resnet101",
        encoder_weights="imagenet",
        in_channels=3,
        classes=1,
        activation=None, 
    )
    return model