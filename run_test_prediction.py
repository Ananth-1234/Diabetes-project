import utils.prediction as p
print('PKL_PATH:', p.PKL_PATH)
print('MODEL_FILE_PATH:', p.MODEL_FILE_PATH)
print('model loaded:', bool(p.model))
if p.model is None:
    print('Model variable is None — check logs for load error')
else:
    print('Model type:', type(p.model))
    # Try a sample prediction (example values taken from typical dataset ranges)
    sample = (1, 120, 70, 20, 79, 25.0, 0.471, 33)
    res, prob = p.predict_diabetes(*sample)
    print('sample prediction ->', res, prob)
