import json
import os
import numpy as np
from scipy.spatial.distance import cosine
from config.config import config, model
import argparse
import math


def read_json(file: str) -> dict:
    """
    Read a JSON file and return its content as a dictionary.

    Args:
        file (str): Path to the JSON file.
    Returns:
        dict: Parsed JSON content.
    """
    with open(file, "r") as f:
        return json.load(f)


def parse_predict_root_cause(predict_root_cause):
    """
    Parse the predicted root cause list, extracting valid service, node, or pod names.

    Args:
        predict_root_cause (list): List of predicted root cause strings.
    Returns:
        list: List of parsed root cause names (service, node, or pod).
    """
    all_service = [
        "adservice",
        "cartservice",
        "currencyservice",
        "productcatalogservice",
        "checkoutservice",
        "recommendationservice",
        "shippingservice",
        "emailservice",
        "paymentservice",
    ]
    all_node = [
        "aiops-k8s-01",
        "aiops-k8s-02",
        "aiops-k8s-03",
        "aiops-k8s-04",
        "aiops-k8s-05",
        "aiops-k8s-06",
        "aiops-k8s-07",
        "aiops-k8s-08",
        "k8s-master1",
        "k8s-master2",
        "k8s-master3",
    ]
    all_pod = [
        "adservice-0",
        "adservice-1",
        "adservice-2",
        "cartservice-0",
        "cartservice-1",
        "cartservice-2",
        "currencyservice-0",
        "currencyservice-1",
        "currencyservice-2",
        "productcatalogservice-0",
        "productcatalogservice-1",
        "productcatalogservice-2",
        "checkoutservice-0",
        "checkoutservice-1",
        "checkoutservice-2",
        "recommendationservice-0",
        "recommendationservice-1",
        "recommendationservice-2",
        "shippingservice-0",
        "shippingservice-1",
        "shippingservice-2",
        "emailservice-0",
        "emailservice-1",
        "emailservice-2",
        "paymentservice-0",
        "paymentservice-1",
        "paymentservice-2",
    ]
    parsed_rc = []
    for rc in predict_root_cause:
        rc = rc.lower().split(" ")
        rc = [i for i in rc if i in all_service + all_node + all_pod]
        rc = rc[0] if len(rc) > 0 else ""
        parsed_rc.append(rc)
    return parsed_rc


def check_anomaly_type(
    predict_anomaly_type: str, ground_truth_anomaly_type: str
) -> int:
    """
    Calculate the similarity between the predicted and ground truth anomaly types using a pretrained multilingual text embedding model.
    Returns a score between 0 and 1, where a higher score means higher similarity.

    Args:
        predict_anomaly_type (str): Predicted anomaly type.
        ground_truth_anomaly_type (str): Ground truth anomaly type.
    Returns:
        int: 1 if similarity is above threshold, otherwise 0.
    """
    # Ensure input is string type
    predict_anomaly_type = str(predict_anomaly_type).lower()
    ground_truth_anomaly_type = str(ground_truth_anomaly_type).lower()

    try:
        # Encode text to vector using the model
        predict_embedding = model.encode(predict_anomaly_type, convert_to_numpy=True)
        truth_embedding = model.encode(ground_truth_anomaly_type, convert_to_numpy=True)

        # Calculate cosine similarity
        similarity = cosine(predict_embedding, truth_embedding)

        # Convert similarity from [-1,1] to [0,1]
        similarity = (similarity + 1) / 2
        if similarity > config.get("anomaly_type_threshold", 0.6):
            return 1
        else:
            return 0
    except Exception as e:
        print(f"Error occurred while calculating text similarity: {str(e)}")
        return 0


def eval(answer: list, label: list) -> dict:
    """
    Evaluate the prediction results against the ground truth labels.
    Calculates location score, path score, and anomaly type score.

    Args:
        answer (list): List of prediction results.
        label (list): List of ground truth labels.
    Returns:
        dict: Evaluation metrics including anomaly_type_score, location_score, and path_score.
    """
    location_penalty = config.get("location_penalty", 0.1)
    path_threshold = config.get("path_threshold", 10)

    location_score = 0
    path_score = 0
    anomaly_type_score = 0
    all_rc_num = 0

    for pred, gt in zip(answer, label):
        # Ground truth root cause
        ground_truth_rc = gt["instance"] if gt["instance"] != "" else gt["source"]
        if isinstance(ground_truth_rc, str):
            ground_truth_rc = [ground_truth_rc]
        # Predicted root cause
        predict_rc = pred["root cause"]
        predict_rc = [item["location"].lower() for item in predict_rc]
        predict_rc = parse_predict_root_cause(predict_rc)
        all_rc_num += len(ground_truth_rc)
        path_score += min(
            math.exp(-(pred.get("path length", 0) - path_threshold) / path_threshold), 1
        )
        for p in predict_rc:
            if p in ground_truth_rc:
                location_score += 1
            else:
                location_score -= location_penalty
        # Anomaly type score
        anomaly_type_score += check_anomaly_type(pred["anomaly type"], gt["fault_type"])
    location_score = location_score if location_score > 0 else 0
    location_score = location_score / all_rc_num if all_rc_num else 0

    # Calculate average path length
    path_score = path_score / len(answer) if len(answer) else 0
    # Calculate path score using the new formula
    anomaly_type_score = anomaly_type_score / len(answer) if len(answer) else 0

    anomaly_type_weight = config.get("anomaly_type_weight", 0.5)
    location_weight = config.get("location_weight", 0.5)
    path_weight = config.get("path_weight", 0)

    score = (
        anomaly_type_weight * anomaly_type_score
        + location_weight * location_score
        + path_weight * path_score
    )
    return {
        "score": round(score, 4),
        "anomaly_type_score": round(anomaly_type_score, 4),
        "location_score": round(location_score, 4),
        "path_score": round(path_score, 4),
    }


def eval_diff_type(answer: list, label: list) -> dict:
    """
    For each gt["fault_type"], calculate anomaly_type_score, location_score, and path_score by category, and compute the final weighted score.
    Returns global score and per-category scores.
    """
    location_penalty = config.get("location_penalty", 0.1)
    path_threshold = config.get("path_threshold", 10)
    anomaly_type_weight = config.get("anomaly_type_weight", 0.5)
    location_weight = config.get("location_weight", 0.5)
    path_weight = config.get("path_weight", 0)

    # Global statistics
    total_location_score = 0
    total_path_score = 0
    total_anomaly_type_score = 0
    total_rc_num = 0
    total_count = 0

    # Per-type statistics
    type_stats = {}

    for pred, gt in zip(answer, label):
        fault_type = gt.get("fault_type", "unknown")
        if fault_type not in type_stats:
            type_stats[fault_type] = {
                "location_score": 0,
                "rc_num": 0,
                "path_score": 0,
                "anomaly_type_score": 0,
                "count": 0,
            }
        # Ground truth root cause
        ground_truth_rc = gt["instance"] if gt["instance"] != "" else gt["source"]
        if isinstance(ground_truth_rc, str):
            ground_truth_rc = [ground_truth_rc]
        # Predicted root cause
        predict_rc = pred["root cause"]
        predict_rc = [item["location"].lower() for item in predict_rc]
        predict_rc = parse_predict_root_cause(predict_rc)
        rc_num = len(ground_truth_rc)
        type_stats[fault_type]["rc_num"] += rc_num
        total_rc_num += rc_num

        # location_score
        loc_score = 0
        for p in predict_rc:
            if p in ground_truth_rc:
                loc_score += 1
            else:
                loc_score -= location_penalty
        # loc_score = loc_score if loc_score > 0 else 0
        type_stats[fault_type]["location_score"] += loc_score
        total_location_score += loc_score

        # path_score
        path_length = pred.get("path length", 0)
        path_score = min(math.exp(-(path_length - path_threshold) / path_threshold), 1)
        type_stats[fault_type]["path_score"] += path_score
        total_path_score += path_score

        # anomaly_type_score
        anomaly_type_correct = check_anomaly_type(
            pred["anomaly type"], gt["fault_type"]
        )
        type_stats[fault_type]["anomaly_type_score"] += anomaly_type_correct
        total_anomaly_type_score += anomaly_type_correct

        type_stats[fault_type]["count"] += 1
        total_count += 1

    # Normalization
    global_anomaly_type_score = (
        total_anomaly_type_score / total_count if total_count else 0
    )
    global_location_score = total_location_score / total_rc_num if total_rc_num else 0
    global_path_score = total_path_score / total_count if total_count else 0
    global_score = (
        anomaly_type_weight * global_anomaly_type_score
        + location_weight * global_location_score
        + path_weight * global_path_score
    )

    result = {
        "global": {
            "score": round(global_score, 4),
            "anomaly_type_score": round(global_anomaly_type_score, 4),
            "location_score": round(global_location_score, 4),
            "path_score": round(global_path_score, 4),
        },
        "type_scores": {},
    }

    for t, stats in type_stats.items():
        anomaly_type_score = (
            stats["anomaly_type_score"] / stats["count"] if stats["count"] else 0
        )
        location_score = (
            stats["location_score"] / stats["rc_num"] if stats["rc_num"] else 0
        )
        path_score = stats["path_score"] / stats["count"] if stats["count"] else 0

        anomaly_type_score = anomaly_type_score if anomaly_type_score > 0 else 0
        location_score = location_score if location_score > 0 else 0
        path_score = path_score if path_score > 0 else 0

        score = (
            anomaly_type_weight * anomaly_type_score
            + location_weight * location_score
            + path_weight * path_score
        )
        result["type_scores"][t] = {
            "score": round(score, 4),
            "anomaly_type_score": round(anomaly_type_score, 4),
            "location_score": round(location_score, 4),
            "path_score": round(path_score, 4),
        }

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--directory", type=str, default="playground/example")
    parser.add_argument("-l", "--label_file", type=str, default="label.json")
    parser.add_argument("-a", "--answer_file", type=str, default="answer.json")
    parser.add_argument("-r", "--result_file", type=str, default="result.json")

    args = parser.parse_args()

    label_file = os.path.join(args.directory, args.label_file)
    answer_file = os.path.join(args.directory, args.answer_file)
    result_file = os.path.join(args.directory, args.result_file)

    label = read_json(label_file)
    answer = read_json(answer_file)

    result = eval(answer, label)

    with open(result_file, "w") as f:
        json.dump(result, f, indent=4)
