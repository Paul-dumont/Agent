import pandas as pd
import json
import numpy as np

def main():
    all_data = []
    list_json = ["beginners", "expert vocab", "missingparam", "normal vocab", "french", "portuguese", "spanish", "short", "long"]
    
    for query in list_json:
        try:
            with open(f"Param_and_cli/results/results_qwen3-8b_{query}_new.json", "r") as f:
                model_results = json.load(f)
            
            for result in model_results:
                model = result.get("model", "Unknown")
                latency = result.get("latency_stats", {})
                
                # On crée un dictionnaire pour chaque métrique pour ce modèle et ce JSON
                metrics = {
                    "total_tests": int(result.get("total_tests")),
                    "avg_tool_selection": np.round(result.get("avg_tool_selection_accuracy"),3),
                    "combined_perfect": int(result.get("combined_perfect")),
                    "param_extraction_perfect": int(result.get("parameter_extraction_perfect")),
                    "avg_param_accuracy": np.round(result.get("avg_parameter_accuracy"),3),
                    "latency_mean": np.round(latency.get("mean_s"),3),
                }
                
                for metric_name, value in metrics.items():
                    all_data.append({
                        "json_file": query,
                        "metric": metric_name,
                        "model": model,
                        "value": value
                    })
        except FileNotFoundError:
            print(f"Fichier results_{query}.json non trouvé.")

    # Création du DataFrame initial
    df_raw = pd.DataFrame(all_data)

    # Pivot pour mettre les modèles en colonnes
    # L'index sera composé du nom du JSON et de la métrique
    df = df_raw.pivot(index=["json_file", "metric"], columns="model", values="value")

    final_rows = []
    # On itère sur les fichiers JSON réellement présents dans le DataFrame
    existing_jsons = df.index.get_level_values(0).unique()
    
    for json_name in existing_jsons:
        # 1. Ajouter le bloc de données du JSON
        group = df.loc[json_name]
        # On remet le nom du JSON dans l'index pour que le concat fonctionne
        group.index = pd.MultiIndex.from_product([[json_name], group.index])
        final_rows.append(group)
        
        # 2. Ajouter la ligne vide séparatrice
        # On utilise une chaîne avec un espace " " pour l'index pour qu'il soit distinct
        empty_index = pd.MultiIndex.from_tuples([(f" ", " ")], names=["json_file", "metric"])
        empty_row = pd.DataFrame("", index=empty_index, columns=df.columns)
        final_rows.append(empty_row)

    # 3. Calcul du bloc TOTAL
    total_data = {}
    metrics_to_sum = ["total_tests", "combined_perfect", "param_extraction_perfect"]
    for metric in df.index.get_level_values(1).unique():
        sub_df = df.xs(metric, level="metric")
        if metric in metrics_to_sum:
            total_data[("TOTAL", metric)] = sub_df.sum()
        else:
            total_data[("TOTAL", metric)] = sub_df.mean().round(3)
            
    df_total = pd.DataFrame.from_dict(total_data, orient='index')
    df_total.index.names = ["json_file", "metric"]
    final_rows.append(df_total)

    # Concaténation finale
    df_final = pd.concat(final_rows)
    
    # Affichage
    print(df_final)
    # Pour sauvegarder en Excel/CSV plus facilement :
    df_final.to_excel("resultats_full_qwen.xlsx")
    return df

if __name__ == "__main__":
    df_final = main()