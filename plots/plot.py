import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from matplotlib.patches import Ellipse

# Configuration du style pour IEEE
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1)

# --- 1. PRÉPARATION DES DONNÉES ---
data = {
    'Models': ['Deepseek-r1 (70B)',	'Gemma3 (12B)',	'GPT-OSS (120B)'	,'Llama3.2 (3B)',	'Mistral-nemo (12B)',	'Nemotron-mini (4B)',	'Phi4 (14B)',	'Qwen3 (8B)']
,
    'Latency': [51.22, 3.98, 40.33, 1.39, 2.64, 1.83, 3.96, 11.21],
    'Perfect_Total': [127, 118, 137, 0, 110, 0, 125, 132],
    'Tool Accuracy': [0.96, 0.93, 0.93, 0.87, 0.84, 0.74, 0.94, 0.97],
    'Parameters Accuracy': [0.83, 0.82, 0.85, 0.00, 0.75, 0.00, 0.81, 0.85],
    # Données pour la Heatmap (Tool Selection Accuracy)
    'Missing Parameters': [0.913, 0.957, 0.783, 0.826, 0.565, 0.696, 0.739, 0.913],
    'Beginners Vocabulary': [0.891, 0.87, 0.87, 0.783, 0.717, 0.711, 0.87, 0.933],
    'Expert Vocabulary': [0.957,1,1,0.957,0.913,0.727,1,0.957],
    'Portuguese' :[0.957,0.909,0.913,0.913,0.87,0.652,0.957,1],
    'Spanish' :[0.957,0.913,0.957,0.826,0.87,0.739,0.957,1],
    'French' :[0.957,0.913,1,0.87,0.87,0.609,0.957,1]


}
df = pd.DataFrame(data)

# --- GRAPHIQUE 1 : SCATTER PLOT (Efficacité Clinique) ---
# plt.figure(figsize=(10, 6))
# scatter = sns.scatterplot(data=df, x='Latency', y='Perfect_Total', s=200, hue='Models', style='Models', palette='viridis')
# plt.title("Clinical Utility Frontier: Latency vs. Success")
# plt.xlabel("Mean Latency (seconds)")
# plt.ylabel("Total Perfect Successes (Tool + Params)")

# circle = Ellipse((10, 122), width=35, height=22, angle=45, fill=False, edgecolor='red', linewidth=2.5, linestyle='--', label='Mid-Scale')
# plt.gca().add_patch(circle)

# circle2 = Ellipse((50, 127), width=35, height=22, angle=135, fill=False, edgecolor='blue', linewidth=2.5, linestyle='--', label='High-Scale')
# plt.gca().add_patch(circle2)

# circle3 = Ellipse((5, 2), width=12, height=17, angle=0, fill=False, edgecolor='green', linewidth=2.5, linestyle='--', label='Edge-Scale')
# plt.gca().add_patch(circle3)

# # Ajouter la légende pour les cercles
# legend = plt.legend(handles =[circle,circle2,circle3], loc='lower right', fontsize=15, title='Models Zones', title_fontsize=20)
# plt.setp(legend.get_title(), fontweight='bold')

# for i in range(df.shape[0]):
#     if df.Models[i] in ['Llama3.2 (3B)']:
#         plt.text(df.Latency[i], df.Perfect_Total[i]+5, df.Models[i], fontsize=10)
#     else:
#         plt.text(df.Latency[i]+1, df.Perfect_Total[i], df.Models[i], fontsize=10)

# plt.tight_layout()
# plt.savefig('scatter_clinical_utility.pdf')
# plt.show()

# --- GRAPHIQUE 2 : BAR CHART (Tool vs Params) ---
# df_melted = df.melt(id_vars='Models', value_vars=['Tool Accuracy', 'Parameters Accuracy'], var_name='Metric', value_name='Accuracy')
# plt.figure(figsize=(12, 6))
# sns.barplot(data=df_melted, x='Models', y='Accuracy', hue='Metric', palette='muted')
# plt.xticks(rotation=45)
# plt.title("Tool Selection vs. Parameter Extraction Accuracy")
# plt.ylim(0, 1.1)
# plt.ylabel("Accuracy Score")
# plt.tight_layout()
# plt.savefig('bar_tool_vs_params.pdf')
# plt.show()

# --- GRAPHIQUE 3 : HEATMAP (Robustesse) ---
heatmap_data = df.set_index('Models')[['Beginners Vocabulary', 'Expert Vocabulary', 'French','Spanish','Portuguese', 'Missing Parameters']]
plt.figure(figsize=(10, 6))
ax=sns.heatmap(heatmap_data, annot=True, cmap='RdYlGn', fmt=".3f", cbar_kws={'label': 'Tool Selection Accuracy'})
ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
plt.title("Model Robustness across Languages and Constraints")
plt.tight_layout()
plt.savefig('heatmap_robust.pdf')
plt.show()