import mysql.connector
from dotenv import load_dotenv
import os
import pandas as pd
import json
import sqlite3
import asyncio
import tqdm
from urllib.parse import urlparse
import random
import warnings
warnings.filterwarnings("ignore")
load_dotenv()


def _prompt_chat_ids() -> list[int]:
    """Ask the user which chat IDs to evaluate at runtime."""
    print("\n┌─────────────────────────────────────────┐")
    print("│        F-LLM Evaluation Runner          │")
    print("└─────────────────────────────────────────┘")
    while True:
        raw = input(
            "Enter chat ID(s) to evaluate (comma-separated, e.g. 1,2,3): "
        ).strip()
        if not raw:
            print("  ✗ No input provided — please enter at least one ID.")
            continue
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        try:
            ids = [int(p) for p in parts]
            if not ids:
                raise ValueError
            print(f"  ✓ Evaluating chat IDs: {ids}\n")
            return ids
        except ValueError:
            print(f"  ✗ '{raw}' contains non-integer values — try again.")

CHAT_IDS: list[int] = _prompt_chat_ids()

def get_mysql_connection():
    conn_str = os.getenv("DB_CONNECTION_SYNC")

    parsed = urlparse(conn_str)

    return mysql.connector.connect(
        host=parsed.hostname,
        port=parsed.port or 3306,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path.lstrip("/")  # removes leading '/'
    )

import pandas as pd

conn = get_mysql_connection()

query = f"""
WITH question_map AS (
    SELECT 
        ROW_NUMBER() OVER (ORDER BY id) AS question_id,
        TRIM(content) AS question_text
    FROM message
    WHERE chat_id = {CHAT_IDS[0]}
      AND role = 'USER'
),
question_answer AS (
    SELECT 
        u.chat_id,
        CONCAT("q",qm.question_id) as question_id,
        u.id AS user_message_id,
        u.content AS user_message,
        (
            SELECT a.id
            FROM message a
            WHERE a.chat_id = u.chat_id
            AND a.role = 'ASSISTANT'
            AND a.id > u.id
            ORDER BY a.id
            LIMIT 1
        ) AS assistant_message_id,
        (
            SELECT a.content
            FROM message a
            WHERE a.chat_id = u.chat_id
            AND a.role = 'ASSISTANT'
            AND a.id > u.id
            ORDER BY a.id
            LIMIT 1
        ) AS assistant_message
    FROM message u
    LEFT JOIN question_map qm 
        ON TRIM(u.content) = qm.question_text
    WHERE u.role = 'USER'
    AND u.chat_id IN ({",".join(map(str, CHAT_IDS))})
)
SELECT  
    qa.chat_id,
    qa.question_id,
    qa.user_message_id,
    qa.user_message,
    qa.assistant_message_id,
    qa.assistant_message,
    (
        SELECT content 
        FROM reasoning_step rs
        WHERE rs.message_id = qa.assistant_message_id
        LIMIT 1
    ) as reasoning_step,
    (
    	SELECT t.llm_model 
        FROM task t
        INNER JOIN chat c ON c.task_id = t.id
        WHERE c.id = qa.chat_id
    ) as model
FROM question_answer qa;
"""

df = pd.read_sql(query, conn)

conn.close()

df["context"] = df["reasoning_step"].apply(
    lambda x: json.loads(x)[0]["contexts"][:5] if x else None
)

df["context_serialized"] = df["context"].apply(
    lambda x: json.dumps(x) if x is not None else None
)

def get_sqlite_connection():
    return sqlite3.connect("evaluation/evaluation.sqlite")

conn = get_sqlite_connection()

conn.execute("""
CREATE TABLE IF NOT EXISTS responses (
    chat_id INTEGER,
    question_id TEXT,
    user_message_id INTEGER,
    user_message TEXT,
    assistant_message_id INTEGER,
    assistant_message TEXT,
    reasoning_step TEXT,
    context TEXT,
    model TEXT,
    UNIQUE(chat_id, question_id, user_message_id, assistant_message_id)
)
""")

conn.commit()
conn.close()


conn = get_sqlite_connection()

conn.execute("""
CREATE TABLE IF NOT EXISTS scores (
    chat_id INTEGER,
    question_id TEXT,
    user_message_id INTEGER,
    assistant_message_id INTEGER,
    context_precision REAL,
    context_recall REAL,
    response_relevancy REAL,
    faithfulness REAL,
    context_relevance REAL,
    response_groundedness REAL,
    model TEXT,
    UNIQUE(chat_id, question_id, user_message_id, assistant_message_id)
)
""")

conn.commit()
conn.close()

conn = get_sqlite_connection()

query = """
INSERT OR IGNORE INTO responses (
    chat_id,
    question_id,
    user_message_id,
    user_message,
    assistant_message_id,
    assistant_message,
    reasoning_step,
    context,
    model
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

# use serialized context
data_to_insert = df[[
    "chat_id",
    "question_id",
    "user_message_id",
    "user_message",
    "assistant_message_id",
    "assistant_message",
    "reasoning_step",
    "context_serialized",
    "model"
]].values.tolist()

conn.executemany(query, data_to_insert)
conn.commit()
conn.close()

conn = get_sqlite_connection()

query = """
INSERT OR IGNORE INTO scores (
    chat_id,
    question_id,
    user_message_id,
    assistant_message_id,
    model
)
VALUES (?, ?, ?, ?, ?)
"""

# use serialized context
data_to_insert = df[[
    "chat_id",
    "question_id",
    "user_message_id",
    "assistant_message_id",
    "model"
]].values.tolist()

conn.executemany(query, data_to_insert)
conn.commit()
conn.close()

def update_scores(chat_id, question_id, user_message_id, assistant_message_id, score_type, score):
    """
    Update a score column for a specific response row.
    
    score_type: str, must be a valid column name in 'scores' table.
    score: value to set
    """
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    # Build SQL query safely using placeholders
    query = f"""
    UPDATE scores
    SET {score_type} = ?
    WHERE chat_id = ?
      AND question_id = ?
      AND user_message_id = ?
      AND assistant_message_id = ?
    """
    
    cursor.execute(query, (score, chat_id, question_id, user_message_id, assistant_message_id))
    conn.commit()
    conn.close()


import logging
from openai import AsyncOpenAI
from ragas.llms import llm_factory
from ragas.embeddings.base import embedding_factory
from ragas.metrics.collections import ContextPrecision
from ragas.metrics.collections import ContextRecall
from ragas.metrics.collections import AnswerRelevancy
from ragas.metrics.collections import Faithfulness
from ragas.metrics.collections import ContextRelevance
from ragas.metrics.collections import ResponseGroundedness


logging.basicConfig(
    filename="evaluation/evaluation.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True
)

logging.basicConfig(level=logging.INFO)

async def evaluate_context_precision(data):
    try:
        client = AsyncOpenAI()
        llm = llm_factory("gpt-5-nano", client=client)

        logging.info(
            f"Calculating Context Precision for {data['chat_id']} & {data['question_id']}"
        )

        # Create metric
        scorer = ContextPrecision(llm=llm)

        # Evaluate
        result = await scorer.ascore(
            user_input=data["user_message"],
            reference=data["assistant_message"],
            retrieved_contexts=data["context"]
        )

        logging.info(f"Completed Context Precision: {result.value}")

        update_scores(data["chat_id"],data["question_id"],data["user_message_id"],data["assistant_message_id"],"context_precision",result.value)
    except Exception as e:
        logging.exception(f"Error in evaluate_context_precision")


async def evaluate_context_recall(data):
    try:
        client = AsyncOpenAI()
        llm = llm_factory("gpt-5-nano", client=client)   

        logging.info(
            f"Calculating Context Recall for {data['chat_id']} & {data['question_id']}"
        )

        # Create metric
        scorer = ContextRecall(llm=llm)

        # Evaluate
        result = await scorer.ascore(
            user_input=data["user_message"],
            reference=data["assistant_message"],
            retrieved_contexts=data["context"]
        )

        logging.info(f"Completed Context Recall: {result.value}")

        update_scores(data["chat_id"],data["question_id"],data["user_message_id"],data["assistant_message_id"],"context_recall",result.value)
    except Exception as e:
        logging.exception(f"Error in evaluate_context_recall")


async def evaluate_response_relevancy(data):
    try:
        embedding_client = AsyncOpenAI()

        client = AsyncOpenAI()
        llm = llm_factory("gpt-5-nano", client=client)

        embeddings = embedding_factory("openai", model="text-embedding-3-small", client=embedding_client)

        logging.info(
            f"Calculating Response Relevancy for {data['chat_id']} & {data['question_id']}"
        )

        # Create metric
        scorer = AnswerRelevancy(llm=llm, embeddings=embeddings)

        # Evaluate
        result = await scorer.ascore(
            user_input=data["user_message"],
            response=data["assistant_message"]
        )

        logging.info(f"Completed Response Relevancy: {result.value}")

        update_scores(data["chat_id"],data["question_id"],data["user_message_id"],data["assistant_message_id"],"response_relevancy",result.value)
    except Exception as e:
        logging.exception(f"Error in evaluate_response_relevancy")


async def evaluate_faithfulness(data):
    try:
        client = AsyncOpenAI()
        llm = llm_factory("gpt-5-nano", client=client)

        logging.info(
            f"Calculating Faithfulness for {data['chat_id']} & {data['question_id']}"
        )

        # Create metric
        scorer = Faithfulness(llm=llm)

        # Evaluate
        result = await scorer.ascore(
            user_input=data["user_message"],
            response=data["assistant_message"],
            retrieved_contexts=data["context"]
        )

        logging.info(f"Completed Faithfulness: {result.value}")

        update_scores(data["chat_id"],data["question_id"],data["user_message_id"],data["assistant_message_id"],"faithfulness",result.value)
    except Exception as e:
        logging.exception(f"Error in evaluate_faithfulness")

async def evaluate_context_relevance(data):
    try:
        client = AsyncOpenAI()
        llm = llm_factory("gpt-5-nano", client=client)

        logging.info(
            f"Calculating Context Relevance for {data['chat_id']} & {data['question_id']}"
        )

        # Create metric
        scorer = ContextRelevance(llm=llm)

        # Evaluate
        result = await scorer.ascore(
            user_input=data["user_message"],
            # response=data["assistant_message"],
            retrieved_contexts=data["context"]
        )

        logging.info(f"Completed Context Relevance: {result.value}")

        update_scores(data["chat_id"],data["question_id"],data["user_message_id"],data["assistant_message_id"],"context_relevance",result.value)
    except Exception as e:
        logging.exception(f"Error in evaluate_context_relevance")


async def evaluate_response_groundedness(data):
    try:
        client = AsyncOpenAI()
        llm = llm_factory("gpt-5-nano", client=client) 

        logging.info(
            f"Calculating Response Groundedness for {data['chat_id']} & {data['question_id']}"
        )

        # Create metric
        scorer = ResponseGroundedness(llm=llm)        

        # Evaluate
        result = await scorer.ascore(
            # user_input=data["user_message"],
            response=data["assistant_message"],
            retrieved_contexts=data["context"]
        )


        logging.info(f"Completed Response Groundedness: {result.value}")

        update_scores(data["chat_id"],data["question_id"],data["user_message_id"],data["assistant_message_id"],"response_groundedness",result.value)
    except Exception as e:
        logging.exception(f"Error in evaluate_response_groundedness")


conn = get_sqlite_connection()
cursor = conn.cursor()

cursor.execute(f"""
SELECT r.* FROM responses as r 
INNER JOIN scores as s 
ON s.chat_id = r.chat_id 
    AND s.question_id = r.question_id 
    AND s.user_message_id = r.user_message_id 
    AND s.assistant_message_id = r.assistant_message_id
WHERE (s.context_precision IS NULL
    OR s.context_recall IS NULL
    OR s.response_relevancy IS NULL
    OR s.faithfulness IS NULL
    OR s.context_relevance IS NULL
    OR s.response_groundedness IS NULL)
    AND r.chat_id IN ({",".join(map(str, CHAT_IDS))})
LIMIT 200
""")

rows = cursor.fetchall()

columns = [description[0] for description in cursor.description]

# Convert rows to list of dicts
dataset = []
for row in rows:
    row_dict = dict(zip(columns, row))
    
    # # Deserialize the context column
    if row_dict.get("context"):
        row_dict["context"] = json.loads(row_dict["context"])
    
    dataset.append(row_dict)

# Close connection
cursor.close()
conn.close()

async def evaluate():
    for data in tqdm.tqdm(dataset):
        await evaluate_context_precision(data)
        await evaluate_context_recall(data)
        await evaluate_context_relevance(data)
        await evaluate_faithfulness(data)
        await evaluate_response_relevancy(data)
        await evaluate_response_groundedness(data)




if __name__ == "__main__":
    import asyncio
    asyncio.run(evaluate())
    

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from matplotlib.patches import FancyBboxPatch
import warnings
warnings.filterwarnings('ignore')


plt.rcdefaults()
# ── Configuration ──
plt.rcParams.update({
    'font.family': 'serif',

    # Base font (everything scales from this)
    'font.size': 18,

    # Titles and labels
    'axes.titlesize': 24,
    'axes.labelsize': 20,

    # Tick labels (important for radar)
    'xtick.labelsize': 18,
    'ytick.labelsize': 16,

    # Legend
    'legend.fontsize': 16,
    'legend.title_fontsize': 18,

    # Figure quality
    'figure.dpi': 300,
    'savefig.dpi': 300,

    # Save layout
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.2,
})

RESULTS_DIR = "evaluation/results"

if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

conn = get_sqlite_connection()

df = pd.read_sql("SELECT * FROM scores", conn)

conn.close()



df['model_short'] = df['model']

metrics_ragas = ['context_precision', 'context_recall', 'response_relevancy', 'faithfulness']
metrics_nvidia = ['context_relevance', 'response_groundedness']
all_metrics = metrics_ragas + metrics_nvidia

metric_labels = {
    'context_precision': 'Context\nPrecision',
    'context_recall': 'Context\nRecall',
    'response_relevancy': 'Response\nRelevancy',
    'faithfulness': 'Faithfulness',
    'context_relevance': 'Context\nRelevance',
    'response_groundedness': 'Response\nGroundedness',
}

metric_labels_flat = {
    'context_precision': 'Context Precision',
    'context_recall': 'Context Recall',
    'response_relevancy': 'Response Relevancy',
    'faithfulness': 'Faithfulness',
    'context_relevance': 'Context Relevance',
    'response_groundedness': 'Response Groundedness',
}


models = df['model_short'].unique()

def random_color():
    return "#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)])

# Sort questions numerically
df['q_num'] = df['question_id'].str.replace('q', '').astype(int)
df = df.sort_values(['model_short', 'q_num'])

# # ── 1. Overall Mean Comparison (Grouped Bar Chart) ──
# fig, ax = plt.subplots(figsize=(14, 7))
means = (
    df.groupby('model_short')[all_metrics]
      .apply(lambda g: g.apply(pd.to_numeric, errors='coerce'))
      .groupby(level=0)
      .mean()
)
stds = df.groupby('model_short')[all_metrics].std()

# ── 2. Radar Chart ──
fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))
angles = np.linspace(0, 2 * np.pi, len(all_metrics), endpoint=False).tolist()
angles += angles[:1]

for model in models:
    values = means.loc[model, all_metrics].tolist()
    values += values[:1]
    ax.plot(angles, values, 'o-', linewidth=2, label=model, markersize=5)
    ax.fill(angles, values, alpha=0.1)

ax.set_xticks(angles[:-1])
ax.set_xticklabels([metric_labels_flat[m] for m in all_metrics], size=14)
ax.set_ylim(0, 1)
ax.tick_params(axis='x', pad=20)
ax.set_title('Radar Comparison of Mean Scores', pad=20)
# ax.legend(loc='lower right', bbox_to_anchor=(0.0, 0.0))
plt.legend(
    loc='upper center', 
    bbox_to_anchor=(0.5, -0.1), # 0.5 centers it, -0.1 puts it below the plot
    ncol=3,                     # Set this to the number of items (3) for a single line
    frameon=False,              # Optional: removes the box for a cleaner look
)
plt.tight_layout()
plt.savefig(f"{RESULTS_DIR}/fig2_radar_comparison.png")
# plt.savefig(f"{RESULTS_DIR}/fig3_radar_comparison.pdf")
plt.close()
print("✓ Fig 1: Radar chart")

# ── 4. Box Plots per Metric ──
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
axes = axes.flatten()

for idx, metric in enumerate(all_metrics):
    ax = axes[idx]
    data_list = [
        df[df['model_short'] == m][metric]
          .dropna()
          .astype(float)
          .values
        for m in models
    ]
    # Skip this metric entirely if every model has no data
    if all(len(d) == 0 for d in data_list):
        ax.set_visible(False)
        continue
    bp = ax.boxplot(data_list, labels=models, patch_artist=True, widths=0.6,
                    medianprops=dict(color='black', linewidth=1.5))
    for patch, model in zip(bp['boxes'], models):
        patch.set_facecolor(random_color())
        patch.set_alpha(0.7)
    ax.set_title(metric_labels_flat[metric])
    ax.set_ylim(-0.05, 1.1)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='x', rotation=15)

fig.suptitle('Score Distributions by Metric and Model', fontsize=18, y=1.01)
plt.tight_layout()
plt.savefig(f"{RESULTS_DIR}/fig3_boxplots.png")
# plt.savefig(f"{RESULTS_DIR}/fig3_boxplots.pdf")
plt.close()
print("✓ Fig 2: Box plots")

# ── 3. Combined Heatmap (Models x Metrics, mean scores) ──
fig, ax = plt.subplots(figsize=(12, 5))
summary = means.loc[models, all_metrics].apply(pd.to_numeric, errors='coerce').fillna(0)
im = ax.imshow(summary.values.astype(float), cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
ax.set_xticks(range(len(all_metrics)))
ax.set_xticklabels([metric_labels_flat[m] for m in all_metrics], rotation=30, ha='right')
ax.set_yticks(range(len(models)))
ax.set_yticklabels(models)
ax.set_title('Mean Scores Summary (Models × Metrics)')
cbar = plt.colorbar(im, ax=ax, shrink=0.8)
cbar.set_label('Mean Score')

for i in range(len(models)):
    for j in range(len(all_metrics)):
        val = summary.values[i, j]
        text_color = 'white' if val < 0.4 else 'black'
        ax.text(j, i, f'{val:.3f}', ha='center', va='center',
                fontsize=18, fontweight='bold', color=text_color)

plt.tight_layout()
plt.savefig(f"{RESULTS_DIR}/fig4_summary_heatmap.png")
# plt.savefig(f"{RESULTS_DIR}/fig7_summary_heatmap.pdf")
plt.close()
print("✓ Fig 3: Summary heatmap")


print("\n" + "=" * 70)
print("SUMMARY TABLE")
print("=" * 70)
summary_df = means.loc[models, all_metrics].round(4)
summary_df['RAGAS_avg'] = summary_df[metrics_ragas].mean(axis=1).round(4)
summary_df['NVIDIA_avg'] = summary_df[metrics_nvidia].mean(axis=1).round(4)
summary_df['Overall_avg'] = summary_df[all_metrics].mean(axis=1).round(4)
print(summary_df.to_string())
print("\nAll visualizations saved to results/")
