# 提交脚本使用指南

本指南介绍如何在竞赛中向评测服务器提交答案。该脚本允许您提交一个答案文件，并在操作成功时获得提交 ID。

## 环境要求

在开始之前，请确保您的系统已安装 Python 3。

## 脚本概览

脚本接受一个 JSON Lines 文件（`*.jsonl`），每行是一个单独的 JSON 对象，代表一个问题回答。

## 命令行提交

要从命令行使用该脚本，请切换到该脚本所在目录，用 Python 运行该脚本：

```bash
python submit.py [-h] [-s SERVER] [-c CONTEST] [-k TICKET] [result_path]
```

* `[result_path]`：提交的结果文件路径。如果未指定，默认使用当前目录下的 `result.jsonl`。
* `-s, --server`：指定评测服务器的 URL。如果未提供，将使用脚本中定义的 `JUDGE_SERVER` 变量。
* `-c, --contest`：比赛标识。如果未提供，将使用脚本中定义的 `CONTEST` 变量。
* `-k, --ticket`：团队标识。如果未提供，将使用脚本中定义的 `TICKET` 变量。

## 编程方式提交

您还可以将 `submit` 函数导入到您的 Python 代码中，以便用编程方式提交数据。


1. 导入函数：
    确保提交脚本位于您的项目目录或 Python 路径中。使用以下方式导入 submit 函数：

    ```python3
    from submit import submit
    ```

2. 调用 submit 函数：
    准备您的提交数据为字典列表，每个字典代表一个要提交的问题回答。调用 submit 函数：

    ```python3
    data = [
        {'anomaly type': '', 'root cause': [{'location': '', 'reason': ''}], 'reasoning trace': [{'step': 0, 'action': '', 'observation': ''}], 'path length': 0}
        # 根据需要添加更多项
    ]

    submission_id = submit(data, judge_server='http://judge.aiops-challenge.com', contest='YOUR_CONTEST_ID', ticket='YOUR_TEAM_TICKET')
    if submission_id:
        print("提交成功！提交 ID: ", submission_id)
    else:
        print("提交失败")
    ```
    
    在此示例中，请将 `YOUR_CONTEST_ID` 替换为您参加的**比赛ID**，将 `YOUR_TEAM_TICKET` 替换为您的**团队ID**。
    *  **比赛ID** 在比赛的URL中获得，比如"赛道一（Qwen1.5-14B）：基于检索增强的运维知识问答挑战赛"的URL为https://competition.aiops-challenge.com/home/competition/1771009908746010681 ，比赛ID为1771009908746010681
    *  **团队ID**需要在参加比赛并组队后能获得，具体在比赛详情页-> 团队 -> 团队ID，为一串数字标识。 

