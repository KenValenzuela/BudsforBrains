import json, time, uuid, os

LOG_PATH = os.path.join("memory", "feedback.jsonl")

def log_feedback(query_vec, strain_id, reward: float):
    record = {
        "id": uuid.uuid4().hex,
        "ts": time.time(),
        "strain_id": strain_id,
        "reward": reward,
        "query_vec": query_vec.tolist(),
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")
