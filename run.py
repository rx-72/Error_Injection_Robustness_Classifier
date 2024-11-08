import os
import json
import pandas as pd
import argparse
import matplotlib.pyplot as plt
import warnings
from sklearn.exceptions import DataConversionWarning
from etl import *

warnings.filterwarnings('ignore')
warnings.filterwarnings(action='ignore', category=DataConversionWarning)

with open("data-params.json", "r") as f:
  params = json.load(f)

METRICS = {
    "accuracy": accuracy
}


def run_baseline_test(X_train, y_train, X_test, y_test, output_dir, args):
  print("")
  print("Running baseline on ZORRO.")
  print("")
  robustness_dicts = []
  for seed in range(5):
    # mpg +- 2 is robust
    robustness_radius = 2
    label_range = (y_train.max()-y_train.min())
    ratios = [0.05, 0.10, 0.15, 0.2, 0.25]
    uncertain_radiuses = [ratio*label_range for ratio in ratios]
    uncertain_pcts = list(np.arange(1, 11)/100)
    robustness_dict = dict()
    robustness_dict['uncertain_radius'] = uncertain_radiuses
    robustness_dict['uncertain_radius_ratios'] = ratios
    for uncertain_pct in tqdm(uncertain_pcts, desc='Progess'):
        robustness_dict[uncertain_pct] = list()
        uncertain_num = int(uncertain_pct*len(y_train))
        for uncertain_radius in tqdm(uncertain_radiuses, desc=f'Varying Uncertain Radius'):

            robustness_ratio = compute_robustness_ratio_label_error(X_train, y_train, X_test, y_test, 
                                                                    uncertain_num=uncertain_num, 
                                                                    uncertain_radius=uncertain_radius, 
                                                                    robustness_radius=robustness_radius, 
                                                                    interval=False, seed=seed)
            robustness_dict[uncertain_pct].append(robustness_ratio)
    robustness_dicts.append(robustness_dict)

  robustness_zonotope_mean = sum([pd.DataFrame(robustness_dicts[i]).iloc[:, 2:] for i in range(5)])/5
  robustness_zonotope_std = (sum([(pd.DataFrame(robustness_dicts[i]).iloc[:, 2:]-robustness_zonotope_mean)**2 for i in range(5)])/5).apply(np.sqrt)

  print()
  print("Running baseline on Meyer.")
  print()
  # Running results with parameter adjustments on Meyer
  robustness_dicts = []
  for seed in range(5):
    # mpg +- 2 is robust
    robustness_radius = 2
    label_range = (y_train.max()-y_train.min())
    ratios = [0.05, 0.10, 0.15, 0.2, 0.25]
    uncertain_radiuses = [ratio*label_range for ratio in ratios]
    uncertain_pcts = list(np.arange(1, 11)/100)
    robustness_dict = dict()
    robustness_dict['uncertain_radius'] = uncertain_radiuses
    robustness_dict['uncertain_radius_ratios'] = ratios
    for uncertain_pct in tqdm(uncertain_pcts, desc='Progess'):
        robustness_dict[uncertain_pct] = list()
        uncertain_num = int(uncertain_pct*len(y_train))
        for uncertain_radius in tqdm(uncertain_radiuses, desc=f'Varying Uncertain Radius'):
            #print(uncertain_radius)
            robustness_ratio = compute_robustness_ratio_label_error(X_train, y_train, X_test, y_test, 
                                                                    uncertain_num=uncertain_num, 
                                                                    uncertain_radius=uncertain_radius, 
                                                                    robustness_radius=robustness_radius, 
                                                                    interval=True, seed=seed)
            robustness_dict[uncertain_pct].append(robustness_ratio)
    robustness_dicts.append(robustness_dict)

  robustness_interval_mean = sum([pd.DataFrame(robustness_dicts[i]).iloc[:, 2:] for i in range(5)])/5
  robustness_interval_std = (sum([(pd.DataFrame(robustness_dicts[i]).iloc[:, 2:]-robustness_interval_mean)**2 for i in range(5)])/5).apply(np.sqrt)

  print("Heatmaps")
  df = robustness_interval_mean

  print("Isolate the portion of the DataFrame for heatmap (exclude the first two columns)")
  heatmap_data = df.multiply(100).values  # Convert fractions to percentages

  print("Labels for x-axis and y-axis")
  x_labels = df.columns.tolist()
  y_labels = [0.05, 0.10, 0.15, 0.2, 0.25]
  
  print("Create the heatmap plot")
  # fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 4), sharey=True, dpi=200)
  fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 3), dpi=200)
  # cmap = plt.get_cmap("coolwarm")
  cmap = plt.get_cmap("autumn_r")
  heatmap = ax1.imshow(heatmap_data, cmap=cmap, interpolation='nearest', aspect='auto', 
                       alpha=0.8, vmin=0, vmax=100)
  
  # Add color bar
  # cbar = plt.colorbar(heatmap, ax=ax1)
  # cbar.set_label('% Percentage')
  
  print("Add white lines by adjusting the linewidth for minor ticks to create separation")
  ax1.set_xticks(np.arange(len(x_labels)) - 0.5, minor=True)
  ax1.set_yticks(np.arange(len(y_labels)) - 0.5, minor=True)
  ax1.grid(which="minor", color="white", linestyle='-', linewidth=0.5)
  ax1.tick_params(which="minor", size=0)
  
  print("Set major ticks for labels without ticks")
  ax1.set_xticks(np.arange(len(x_labels)))
  ax1.set_yticks(np.arange(len(y_labels)))
  ax1.set_xticklabels(x_labels)
  ax1.set_yticklabels(y_labels)
  ax1.tick_params(axis='both', which='both', length=0)  # Remove tick marks
  
  print("Remove external boundaries")
  ax1.spines['top'].set_visible(False)
  ax1.spines['right'].set_visible(False)
  ax1.spines['left'].set_visible(False)
  ax1.spines['bottom'].set_visible(False)
  
  print("Set axis labels")
  ax1.set_xlabel('Percentage of Uncertain Data', fontsize=12)
  ax1.set_ylabel('Uncertain Radius (%)', fontsize=12)
  
  print("Add text annotations")
  for i in range(len(y_labels)):
      for j in range(len(x_labels)):
          if heatmap_data[i][j]==100:
              text = ax1.text(j, i, f'{heatmap_data[i][j]:.0f}', ha='center', va='center', color='black')
          elif heatmap_data[i][j]==0:
              text = ax1.text(j, i, '0', ha='center', va='center', color='black')
          else:
              text = ax1.text(j, i, f'{heatmap_data[i][j]:.1f}', ha='center', va='center', color='black')
  ax1.set_title('Meyer et al.')
  
  df = robustness_zonotope_mean
  
  print("Isolate the portion of the DataFrame for heatmap (exclude the first two columns)")
  heatmap_data = df.multiply(100).values  # Convert fractions to percentages
  heatmap2 = ax2.imshow(heatmap_data, cmap=cmap, interpolation='nearest', 
                        aspect='auto', alpha=0.8, vmin=0, vmax=100)
  
  print("Add color bar")
  # cbar.set_label('% Percentage')
  
  print("Add white lines by adjusting the linewidth for minor ticks to create separation")
  ax2.set_xticks(np.arange(len(x_labels)) - 0.5, minor=True)
  ax2.set_yticks(np.arange(len(y_labels)) - 0.5, minor=True)
  ax2.grid(which="minor", color="white", linestyle='-', linewidth=0.5)
  ax2.tick_params(which="minor", size=0)
  
  print("Set major ticks for labels without ticks")
  ax2.set_xticks(np.arange(len(x_labels)))
  ax2.set_yticks(np.arange(len(y_labels)))
  ax2.set_xticklabels(x_labels)
  ax2.set_yticklabels(y_labels)
  ax2.tick_params(axis='both', which='both', length=0)  # Remove tick marks
  
  print("Remove external boundaries")
  ax2.spines['top'].set_visible(False)
  ax2.spines['right'].set_visible(False)
  ax2.spines['left'].set_visible(False)
  ax2.spines['bottom'].set_visible(False)
  
  print("Set axis labels")
  ax2.set_xlabel('Percentage of Uncertain Data', fontsize=12)
  ax2.set_ylabel('Uncertain Radius (%)', fontsize=12)
  
  print("Add text annotations")
  for i in range(len(y_labels)):
      for j in range(len(x_labels)):
          if heatmap_data[i][j]==100:
              text = ax2.text(j, i, '100', ha='center', va='center', color='black')
          elif heatmap_data[i][j]==0:
              text = ax2.text(j, i, '0', ha='center', va='center', color='black')
          else:
              text = ax2.text(j, i, f'{np.around(heatmap_data[i][j], 1)}', ha='center', 
                              va='center', color='black')
  ax2.set_title('ZORRO')
  print("Final edits")
  # fig.suptitle('Robustness Ratio (%)', fontsize=14)
  plt.subplots_adjust(wspace=0.2, bottom=0.2, left=0.1, right=0.9)
  cb = fig.colorbar(heatmap2, ax=(ax1, ax2), orientation='vertical', pad=0.02)
  cb.set_label('Robustness Ratio (%)', fontsize=12)
  plt.savefig(f"{output_dir}/{args.dataset}-baseline-label-heatmap.pdf", bbox_inches='tight')

  print("")
  print("Making line plot...")
  print("")
  uncertain_pcts = np.array([0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1])*100
  uncertain_radius_ratios = [0.05, 0.10, 0.15, 0.2, 0.25]

  zonotope_data_mean_dict = dict()
  zonotope_data_std_dict = dict()
  for i, radius_ratio in enumerate(uncertain_radius_ratios):
    zonotope_data_mean_dict[radius_ratio] = np.append([1], robustness_zonotope_mean.iloc[i, :].to_numpy())
    zonotope_data_std_dict[radius_ratio] = np.append([0], robustness_zonotope_std.iloc[i, :].to_numpy())

  interval_data_mean_dict = dict()
  interval_data_std_dict = dict()
  for i, radius_ratio in enumerate(uncertain_radius_ratios):
    interval_data_mean_dict[radius_ratio] = np.append([1], robustness_interval_mean.iloc[i, :].to_numpy())
    interval_data_std_dict[radius_ratio] = np.append([0], robustness_interval_std.iloc[i, :].to_numpy())
    
  fig, axes = plt.subplots(nrows=1, ncols=4, figsize=(12, 2), sharex=True, dpi=200)

  for i in range(4):
    uncertain_radius_ratio = uncertain_radius_ratios[i]
    axes[i].errorbar(uncertain_pcts, zonotope_data_mean_dict[uncertain_radius_ratio],
                     yerr=3*zonotope_data_std_dict[uncertain_radius_ratio],
                     marker='o', color='red', label='ZORRO', linestyle='-')
    axes[i].errorbar(uncertain_pcts, interval_data_mean_dict[uncertain_radius_ratio],
                     yerr=3*interval_data_std_dict[uncertain_radius_ratio],
                     marker='s', color='green', label='Meyer et al.', linestyle='--')
    axes[i].set_title(f'Uncertain Radius: {int(uncertain_radius_ratio*100)} %')
    if i == 0:
        axes[i].set_ylabel('Robustness Ratio', fontsize=12)
    axes[i].set_ylim(-0.05, 1.05)
    axes[i].grid(True)

  print("Adjust layout")
  lines_labels = [axes[0].get_legend_handles_labels()]
  lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
  fig.legend(lines, labels, loc = (0.73, 0.03), ncol=2, frameon=False)

  plt.subplots_adjust(wspace=0.2, top=0.8, bottom=0.25, left=0.1, right=0.9)
  fig.supxlabel('Uncertain Data Percentage (%)', fontsize=12, verticalalignment='bottom')
  # plt.tight_layout()
  # plt.show()
  plt.savefig(f"{output_dir}/{args.dataset}-baseline-label-lineplot.pdf", bbox_inches='tight')
  
  print("")
  print("Baseline finished!")
  print("")

def run_complex_test(X_train, y_train, X_test, y_test, output_dir, metric, modeltype, args, maximize=True):
  print("")
  print(f"Generating important indices based on {args.metric}:")
  print("")

  X_train, X_test, y_train, y_test = X_train.reset_index(drop=True) , X_test.reset_index(drop=True) , y_train.reset_index(drop=True) , y_test.reset_index(drop=True)
  boundary_indices = leave_one_out(X_train, y_train, X_test, y_test, modeltype, metric, maximize)
  

  print("")
  print(f"Running complex (using {args.metric}) on ZORRO.")
  print("")
  robustness_dicts = []
  for seed in range(5):
    # mpg +- 2 is robust
    robustness_radius = 2
    label_range = (y_train.max()-y_train.min())
    ratios = [0.05, 0.10, 0.15, 0.2, 0.25]
    uncertain_radiuses = [ratio*label_range for ratio in ratios]
    uncertain_pcts = list(np.arange(1, 11)/100)
    robustness_dict = dict()
    robustness_dict['uncertain_radius'] = uncertain_radiuses
    robustness_dict['uncertain_radius_ratios'] = ratios
    for uncertain_pct in tqdm(uncertain_pcts, desc='Progess'):
        robustness_dict[uncertain_pct] = list()
        uncertain_num = int(uncertain_pct*len(y_train))
        for uncertain_radius in tqdm(uncertain_radiuses, desc=f'Varying Uncertain Radius'):

            robustness_ratio = compute_robustness_ratio_sensitive_label_error(X_train, y_train, X_test, y_test, 
                                                                    uncertain_num=uncertain_num,
                                                                    boundary_indices=boundary_indices,
                                                                    uncertain_radius=uncertain_radius, 
                                                                    robustness_radius=robustness_radius, 
                                                                    interval=False, seed=seed)
            robustness_dict[uncertain_pct].append(robustness_ratio)
    robustness_dicts.append(robustness_dict)

  robustness_zonotope_mean = sum([pd.DataFrame(robustness_dicts[i]).iloc[:, 2:] for i in range(5)])/5
  robustness_zonotope_std = (sum([(pd.DataFrame(robustness_dicts[i]).iloc[:, 2:]-robustness_zonotope_mean)**2 for i in range(5)])/5).apply(np.sqrt)

  print()
  print(f"Running complex (using {args.metric}) on Meyer.")
  print()
  # Running results with parameter adjustments on Meyer
  robustness_dicts = []
  for seed in range(5):
    # mpg +- 2 is robust
    robustness_radius = 2
    label_range = (y_train.max()-y_train.min())
    ratios = [0.05, 0.10, 0.15, 0.2, 0.25]
    uncertain_radiuses = [ratio*label_range for ratio in ratios]
    uncertain_pcts = list(np.arange(1, 11)/100)
    robustness_dict = dict()
    robustness_dict['uncertain_radius'] = uncertain_radiuses
    robustness_dict['uncertain_radius_ratios'] = ratios
    for uncertain_pct in tqdm(uncertain_pcts, desc='Progess'):
        robustness_dict[uncertain_pct] = list()
        uncertain_num = int(uncertain_pct*len(y_train))
        for uncertain_radius in tqdm(uncertain_radiuses, desc=f'Varying Uncertain Radius'):
            #print(uncertain_radius)
            robustness_ratio = compute_robustness_ratio_sensitive_label_error(X_train, y_train, X_test, y_test, 
                                                                    uncertain_num=uncertain_num,
                                                                    boundary_indices=boundary_indices,
                                                                    uncertain_radius=uncertain_radius, 
                                                                    robustness_radius=robustness_radius, 
                                                                    interval=False, seed=seed)
            robustness_dict[uncertain_pct].append(robustness_ratio)
    robustness_dicts.append(robustness_dict)

  robustness_interval_mean = sum([pd.DataFrame(robustness_dicts[i]).iloc[:, 2:] for i in range(5)])/5
  robustness_interval_std = (sum([(pd.DataFrame(robustness_dicts[i]).iloc[:, 2:]-robustness_interval_mean)**2 for i in range(5)])/5).apply(np.sqrt)

  print("Heatmaps")
  df = robustness_interval_mean

  print("Isolate the portion of the DataFrame for heatmap (exclude the first two columns)")
  heatmap_data = df.multiply(100).values  # Convert fractions to percentages

  print("Labels for x-axis and y-axis")
  x_labels = df.columns.tolist()
  y_labels = [0.05, 0.10, 0.15, 0.2, 0.25]
  
  print("Create the heatmap plot")
  # fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 4), sharey=True, dpi=200)
  fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 3), dpi=200)
  # cmap = plt.get_cmap("coolwarm")
  cmap = plt.get_cmap("autumn_r")
  heatmap = ax1.imshow(heatmap_data, cmap=cmap, interpolation='nearest', aspect='auto', 
                       alpha=0.8, vmin=0, vmax=100)
  
  # Add color bar
  # cbar = plt.colorbar(heatmap, ax=ax1)
  # cbar.set_label('% Percentage')
  
  print("Add white lines by adjusting the linewidth for minor ticks to create separation")
  ax1.set_xticks(np.arange(len(x_labels)) - 0.5, minor=True)
  ax1.set_yticks(np.arange(len(y_labels)) - 0.5, minor=True)
  ax1.grid(which="minor", color="white", linestyle='-', linewidth=0.5)
  ax1.tick_params(which="minor", size=0)
  
  print("Set major ticks for labels without ticks")
  ax1.set_xticks(np.arange(len(x_labels)))
  ax1.set_yticks(np.arange(len(y_labels)))
  ax1.set_xticklabels(x_labels)
  ax1.set_yticklabels(y_labels)
  ax1.tick_params(axis='both', which='both', length=0)  # Remove tick marks
  
  print("Remove external boundaries")
  ax1.spines['top'].set_visible(False)
  ax1.spines['right'].set_visible(False)
  ax1.spines['left'].set_visible(False)
  ax1.spines['bottom'].set_visible(False)
  
  print("Set axis labels")
  ax1.set_xlabel('Percentage of Uncertain Data', fontsize=12)
  ax1.set_ylabel('Uncertain Radius (%)', fontsize=12)
  
  print("Add text annotations")
  for i in range(len(y_labels)):
      for j in range(len(x_labels)):
          if heatmap_data[i][j]==100:
              text = ax1.text(j, i, f'{heatmap_data[i][j]:.0f}', ha='center', va='center', color='black')
          elif heatmap_data[i][j]==0:
              text = ax1.text(j, i, '0', ha='center', va='center', color='black')
          else:
              text = ax1.text(j, i, f'{heatmap_data[i][j]:.1f}', ha='center', va='center', color='black')
  ax1.set_title('Meyer et al.')
  
  df = robustness_zonotope_mean
  
  print("Isolate the portion of the DataFrame for heatmap (exclude the first two columns)")
  heatmap_data = df.multiply(100).values  # Convert fractions to percentages
  heatmap2 = ax2.imshow(heatmap_data, cmap=cmap, interpolation='nearest', 
                        aspect='auto', alpha=0.8, vmin=0, vmax=100)
  
  print("Add color bar")
  # cbar.set_label('% Percentage')
  
  print("Add white lines by adjusting the linewidth for minor ticks to create separation")
  ax2.set_xticks(np.arange(len(x_labels)) - 0.5, minor=True)
  ax2.set_yticks(np.arange(len(y_labels)) - 0.5, minor=True)
  ax2.grid(which="minor", color="white", linestyle='-', linewidth=0.5)
  ax2.tick_params(which="minor", size=0)
  
  print("Set major ticks for labels without ticks")
  ax2.set_xticks(np.arange(len(x_labels)))
  ax2.set_yticks(np.arange(len(y_labels)))
  ax2.set_xticklabels(x_labels)
  ax2.set_yticklabels(y_labels)
  ax2.tick_params(axis='both', which='both', length=0)  # Remove tick marks
  
  print("Remove external boundaries")
  ax2.spines['top'].set_visible(False)
  ax2.spines['right'].set_visible(False)
  ax2.spines['left'].set_visible(False)
  ax2.spines['bottom'].set_visible(False)
  
  print("Set axis labels")
  ax2.set_xlabel('Percentage of Uncertain Data', fontsize=12)
  ax2.set_ylabel('Uncertain Radius (%)', fontsize=12)
  
  print("Add text annotations")
  for i in range(len(y_labels)):
      for j in range(len(x_labels)):
          if heatmap_data[i][j]==100:
              text = ax2.text(j, i, '100', ha='center', va='center', color='black')
          elif heatmap_data[i][j]==0:
              text = ax2.text(j, i, '0', ha='center', va='center', color='black')
          else:
              text = ax2.text(j, i, f'{np.around(heatmap_data[i][j], 1)}', ha='center', 
                              va='center', color='black')
  ax2.set_title('ZORRO')
  print("Final edits")
  # fig.suptitle('Robustness Ratio (%)', fontsize=14)
  plt.subplots_adjust(wspace=0.2, bottom=0.2, left=0.1, right=0.9)
  cb = fig.colorbar(heatmap2, ax=(ax1, ax2), orientation='vertical', pad=0.02)
  cb.set_label('Robustness Ratio (%)', fontsize=12)
  plt.savefig(f"{output_dir}/{args.dataset}-complex(using {args.metric})-label-heatmap.pdf", bbox_inches='tight')

  print("")
  print("Making line plot...")
  print("")
  uncertain_pcts = np.array([0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1])*100
  uncertain_radius_ratios = [0.05, 0.10, 0.15, 0.2, 0.25]

  zonotope_data_mean_dict = dict()
  zonotope_data_std_dict = dict()
  for i, radius_ratio in enumerate(uncertain_radius_ratios):
    zonotope_data_mean_dict[radius_ratio] = np.append([1], robustness_zonotope_mean.iloc[i, :].to_numpy())
    zonotope_data_std_dict[radius_ratio] = np.append([0], robustness_zonotope_std.iloc[i, :].to_numpy())

  interval_data_mean_dict = dict()
  interval_data_std_dict = dict()
  for i, radius_ratio in enumerate(uncertain_radius_ratios):
    interval_data_mean_dict[radius_ratio] = np.append([1], robustness_interval_mean.iloc[i, :].to_numpy())
    interval_data_std_dict[radius_ratio] = np.append([0], robustness_interval_std.iloc[i, :].to_numpy())
    
  fig, axes = plt.subplots(nrows=1, ncols=4, figsize=(12, 2), sharex=True, dpi=200)

  for i in range(4):
    uncertain_radius_ratio = uncertain_radius_ratios[i]
    axes[i].errorbar(uncertain_pcts, zonotope_data_mean_dict[uncertain_radius_ratio],
                     yerr=3*zonotope_data_std_dict[uncertain_radius_ratio],
                     marker='o', color='red', label='ZORRO', linestyle='-')
    axes[i].errorbar(uncertain_pcts, interval_data_mean_dict[uncertain_radius_ratio],
                     yerr=3*interval_data_std_dict[uncertain_radius_ratio],
                     marker='s', color='green', label='Meyer et al.', linestyle='--')
    axes[i].set_title(f'Uncertain Radius: {int(uncertain_radius_ratio*100)} %')
    if i == 0:
        axes[i].set_ylabel('Robustness Ratio', fontsize=12)
    axes[i].set_ylim(-0.05, 1.05)
    axes[i].grid(True)

  print("Adjust layout")
  lines_labels = [axes[0].get_legend_handles_labels()]
  lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
  fig.legend(lines, labels, loc = (0.73, 0.03), ncol=2, frameon=False)

  plt.subplots_adjust(wspace=0.2, top=0.8, bottom=0.25, left=0.1, right=0.9)
  fig.supxlabel('Uncertain Data Percentage (%)', fontsize=12, verticalalignment='bottom')
  # plt.tight_layout()
  # plt.show()
  plt.savefig(f"{output_dir}/{args.dataset}-complex(using {args.metric})-label-lineplot.pdf", bbox_inches='tight')
  
  print("")
  print("Complex finished!")
  print("")

# Main function to parse arguments
def main():
  # Argument parsing
  print("")
  print("Grabbing Arguments...")
  print("")
  parser = argparse.ArgumentParser(description="Run robustness tests")
  parser.add_argument('--test', choices=['baseline', 'leave_one_out'], help="Specify which test to run: (baseline, leave_one_out)")
  parser.add_argument("--dataset", choices=["cancer", "mpg", "ins"], default="cancer", help="Filename of the datset in the datasets' folder")
  parser.add_argument('--metric', type=str, default="accuracy", help="Metric to use (only for complex test)")
  args = parser.parse_args()

  # Set parameters
  # set parameters
  output_dir = params["output_dir"]
  os.makedirs(output_dir, exist_ok=True)
  metric = args.metric if args.test == "leave_one_out" else None

  
  # Load data
  if args.dataset == "cancer":
    X_train, X_test, y_train, y_test = load_data(random_seed=params["random_seed"])
  elif args.dataset == "mpg":
    X_train, X_test, y_train, y_test = load_mpg_cleaned(random_seed=params["random_seed"])
  elif args.dataset == "ins":
    X_train, X_test, y_train, y_test = load_ins_cleaned(random_seed=params["random_seed"])
  else:
    print("")
    print("Dataset is not provided, please provided dataset.")

  # run chosen test
  if args.test == 'baseline':
    run_baseline_test(X_train, y_train, X_test, y_test, output_dir, args)
  elif args.test == 'leave_one_out':
    if args.dataset == "cancer":
      if metric == "accuracy":
        run_complex_test(X_train, y_train, X_test, y_test, output_dir, accuracy, LogisticRegression, args)
      else:
        run_complex_test(X_train, y_train, X_test, y_test, output_dir, accuracy, LogisticRegression, args)
    elif args.dataset == "mpg":
      if metric == "mae":
        run_complex_test(X_train, y_train, X_test, y_test, output_dir, mae, LinearRegression, args, maximize=False)
      elif metric == "mse":
        run_complex_test(X_train, y_train, X_test, y_test, output_dir, mse, LinearRegression, args, maximize=False)
      elif metric == "rmse":
        run_complex_test(X_train, y_train, X_test, y_test, output_dir, rmse, LinearRegression, args, maximize=False)
      elif metric == "r_squared":
        run_complex_test(X_train, y_train, X_test, y_test, output_dir, r_squared, LinearRegression, args)
      else:
        run_complex_test(X_train, y_train, X_test, y_test, output_dir, mae, LinearRegression, args, maximize=False)
    elif args.dataset == "ins":
      if metric == "mae":
        run_complex_test(X_train, y_train, X_test, y_test, output_dir, mae, LinearRegression, args, maximize=False)
      elif metric == "mse":
        run_complex_test(X_train, y_train, X_test, y_test, output_dir, mse, LinearRegression, args, maximize=False)
      elif metric == "rmse":
        run_complex_test(X_train, y_train, X_test, y_test, output_dir, rmse, LinearRegression, args, maximize=False)
      elif metric == "r_squared":
        run_complex_test(X_train, y_train, X_test, y_test, output_dir, r_squared, LinearRegression, args)
      else:
        run_complex_test(X_train, y_train, X_test, y_test, output_dir, mae, LinearRegression, args, maximize=False)
    else:
        print("")
        print("Not a dataset provided!")
  else:
    print("")
    print("Not a test baseline")
    print("")

if __name__ == "__main__":
  main()


