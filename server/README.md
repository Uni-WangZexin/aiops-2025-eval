# 服务端说明

服务端主要功能包括接收参赛选手的提交，对提交内容进行评测以获取分数，并据此更新排行榜。



## 环境准备

首先请确保您的系统中已安装了 conda，然后通过 conda 创建一个 Python 3.10 环境，并使用 pip 安装所需依赖：


```bash
conda create -n aiops25 python=3.12.6
conda activate aiops25
pip install -r requirements.txt
```

## 评测脚本使用指南

评测脚本文件名为 `eval.py`。


### 配置文件准备

1. 根据配置文件中（`config/config.yaml`）的注释更新配置项。

### 测试脚本执行

运行以下命令以执行示例评测任务：

```bash
python eval.py -d playground/example
```

### 自定义评测

1. 在 `playground` 目录下创建新的文件夹 (如 `xxx`)，并在其中放置 `label.json` (参考答案) 和 `answer.json`(模型生成的答案)。
2. 执行命令 `python eval.py -d playground/xxx` 来获取评测结果。默认情况下，评测结果将保存在 `playground/xxx/result.json` 中。

脚本参数说明：
* `-d, --directory`：工作目录，用于指定包含参考答案和模型答案的文件夹路径。默认为空，即当前目录。
* `-l, --label_file`：参考答案文件的路径。默认为 `label.json`。
* `-a, --answer_file`：模型生成答案文件的路径。默认为 `answer.json`。
* `-r, --result_file`：评测结果将保存在此 JSON 格式的文件中。默认为 `result.json`。
* `--diff_type`：是否针对不同类型的故障分别评估，默认为 `False`。


### 文件格式

模型生成答案文件 (answer file) 应遵循形如下列示例的格式，至少需要包含 `anomaly type`, `root cause`, `reasoning trace`, `path length` 字段：

```json
[
    {
        "anomaly type": "pod kill",
        "root cause": [
            {
                "location": "paymentservice-0",
                "reason": "Critical pod in the service chain with recent restarts"
            },
            {
                "location": "paymentservice-1",
                "reason": "Critical pod in the service chain with recent restarts"
            },
            {
                "location": "paymentservice-2",
                "reason": "Critical pod in the service chain with recent restarts"
            },
            {
                "location": "checkoutservice",
                "reason": "Node hosting paymentservice pods"
            },
            {
                "location": "aiops-k8s-08",
                "reason": "Node hosting paymentservice pods"
            }
        ],
        "reasoning trace": [
            {
                "step": 0,
                "action": "classifier Args: {'start_time': '2025-05-05 10:11:31', 'end_time': '2025-05-05 10:29:31'}",
                "observation": "Main failure type: pod kill"
            },
            {
                "step": 1,
                "action": "match_sop Args: {'query': 'SOP of pod kill', 'threshold': 0.55}",
                "observation": "Matched SOP 1: SOP of Pod Kill\nSimilarity Score: 1.0000\nSOP Content:\n1. Time series anomaly detection of all services in terms of metric request and response. 2. Time series anomaly detection of all pods in terms of metric pod_processes and pod_network_transmit_packets. 3. The result is combination of the previous steps.\nMatched SOP 2: SOP of Pod Failure\nSimilarity Score: 0.8032\nSOP Content:\n1. 2. The result is combination of the previous steps.\n"
            }
        ],
        "token count": 43914,
        "path length": 8
    }
]
```


标签文件 (label file) 应遵循形如下列示例的格式：
```json
[
    {
        "fault_category": "network attack",
        "fault_type": "network delay",
        "instance_type": "service",
        "instance": "checkoutservice",
        "source": "checkoutservice",
        "destination": "currencyservice",
        "start_time": "2025-05-05T10:11:31Z",
        "end_time": "2025-05-05T10:29:31Z",
        "key_observations":["xxx"]
    }
]
```

## 评分方式

我们的评分机制综合考虑了**根因位置准确性**，**根因类型准确率**，**推理效率**和**推理链条合理性**四个层面。

### 根因位置准确性

这个部分，我们重点比较根因位置的准确率。

#### 举例

上述标签文件中，label为`checkoutservice`, 而答案的root cause location为`paymentservice-0`, `paymentservice-1`, `paymentservice-2`, `checkoutservice`, `aiops-k8s-08`。

则 
```
location_score = ([正确根因数目] - location_penaty * [错误根因数目]) / [总根因数目]
location_score = (1 - location_penaty * 4) / 1
```
解释：正确1个，错误四个，总根因数目为1

### 根因类型准确性

这个部分，我们重点比较根因类型（故障类型）的准确率。

#### 举例

上述标签文件中，label为`network delay`, 而answer为`pod kill`
则 
```
anomaly_type_score = 0
# 循环迭代所有
for answer, label in zip(answers, labels):
    anomaly_type_score += 1 if similarity(answer, label) > anomaly_type_threshold else 0
anomaly_type_score = anomaly_type_score / [故障数目]
```
解释：根据向量相似度以及阈值判断是否判断正确，总分数为判断正确的比例。

### 推理效率

这个部分，我们重点关注推理效率。

#### 举例

```
path_score = 0
for fault in faults:
    path_score += min(exp(-(path_length - 10) / 10), 1)
path_score = path_score / [故障数目]
```

### 推理链条合理性

这个部分，我们重点关注推理链条的合理性。

我们对于每个故障，都有一些关键的定位信息。具体评估过程中，利用关键词匹配的方式，计算推理步骤中，是否包含了关键的定位信息。

### 提交得分

队伍的每次提交应包含所有题目的答案，该次提交的得分为所有题目得分的平均值。

### 实现细节

评分机制的详细实现，请参见 `eval.py` 文件，该文件包含了上述评分逻辑的具体代码实现。