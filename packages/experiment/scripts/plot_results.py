#!/usr/bin/env python3
"""Script para gerar visualizações dos resultados do experimento.

Gera gráficos de degradação de tool calling por nível de poluição
para uso no paper do TCC.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Configuração de estilo para paper acadêmico
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.size': 12,
    'font.family': 'serif',
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'legend.fontsize': 11,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'figure.figsize': (10, 6),
    'figure.dpi': 150,
})

def load_data(csv_path: str) -> pd.DataFrame:
    """Carrega dados do CSV exportado."""
    return pd.read_csv(csv_path)


def calculate_success_rate(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula taxa de sucesso por modelo e nível de poluição."""
    summary = df.groupby(['model', 'pollution_level']).agg(
        total=('classification', 'count'),
        success=('classification', lambda x: (x == 'STC').sum()),
    ).reset_index()

    summary['success_rate'] = 100 * summary['success'] / summary['total']
    return summary


def plot_degradation_curve(summary: pd.DataFrame, output_path: str) -> None:
    """Gera gráfico de curva de degradação."""
    fig, ax = plt.subplots(figsize=(10, 6))

    colors = {
        'qwen3:4b': '#2196F3',  # Azul
        'qwen3:8b': '#4CAF50',  # Verde
    }

    markers = {
        'qwen3:4b': 'o',
        'qwen3:8b': 's',
    }

    for model in summary['model'].unique():
        model_data = summary[summary['model'] == model].sort_values('pollution_level')
        ax.plot(
            model_data['pollution_level'],
            model_data['success_rate'],
            marker=markers.get(model, 'o'),
            markersize=10,
            linewidth=2.5,
            label=f'{model} ({model.split(":")[1].upper()})',
            color=colors.get(model, 'gray'),
        )

    ax.set_xlabel('Nível de Poluição do Contexto (%)')
    ax.set_ylabel('Taxa de Sucesso em Tool Calling (%)')
    ax.set_title('Degradação do Tool Calling por Tamanho do Modelo')

    ax.set_xlim(-5, 85)
    ax.set_ylim(-5, 105)
    ax.set_xticks([0, 20, 40, 60, 80])
    ax.set_yticks([0, 25, 50, 75, 100])

    ax.axhline(y=50, color='red', linestyle='--', alpha=0.3, label='Limiar 50%')

    ax.legend(loc='lower left')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.savefig(output_path.replace('.png', '.pdf'), bbox_inches='tight')
    print(f"Gráfico salvo em: {output_path}")
    print(f"Gráfico PDF salvo em: {output_path.replace('.png', '.pdf')}")


def plot_classification_distribution(df: pd.DataFrame, output_path: str) -> None:
    """Gera gráfico de distribuição de classificações."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for idx, model in enumerate(df['model'].unique()):
        model_data = df[df['model'] == model]

        pivot = model_data.groupby(['pollution_level', 'classification']).size().unstack(fill_value=0)

        # Reordena colunas
        cols_order = ['STC', 'FNC', 'FWT', 'FH']
        pivot = pivot.reindex(columns=[c for c in cols_order if c in pivot.columns])

        colors = {'STC': '#4CAF50', 'FNC': '#FFC107', 'FWT': '#FF9800', 'FH': '#F44336'}
        color_list = [colors.get(c, 'gray') for c in pivot.columns]

        pivot.plot(
            kind='bar',
            stacked=True,
            ax=axes[idx],
            color=color_list,
            width=0.7,
        )

        axes[idx].set_title(f'{model}')
        axes[idx].set_xlabel('Nível de Poluição (%)')
        axes[idx].set_ylabel('Número de Execuções')
        axes[idx].set_xticklabels([f'{int(x)}%' for x in pivot.index], rotation=0)
        axes[idx].legend(title='Classificação')
        axes[idx].set_ylim(0, 25)

    plt.suptitle('Distribuição de Classificações por Modelo e Nível de Poluição', fontsize=14)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Gráfico salvo em: {output_path}")


def print_summary_table(summary: pd.DataFrame) -> None:
    """Imprime tabela resumo para o paper."""
    print("\n" + "=" * 70)
    print("TABELA RESUMO PARA O PAPER")
    print("=" * 70)

    pivot = summary.pivot(index='pollution_level', columns='model', values='success_rate')
    pivot.index = [f'{int(x)}%' for x in pivot.index]

    print("\nTaxa de Sucesso (%) por Modelo e Nível de Poluição:")
    print("-" * 50)
    print(pivot.round(1).to_string())
    print("-" * 50)


def main():
    """Função principal."""
    # Paths
    base_path = Path(__file__).parent.parent
    data_path = base_path / 'data' / 'experiment_results.csv'
    output_dir = base_path / 'data' / 'figures'
    output_dir.mkdir(exist_ok=True)

    # Carrega dados
    print(f"Carregando dados de: {data_path}")
    df = load_data(str(data_path))
    print(f"Total de registros: {len(df)}")

    # Calcula métricas
    summary = calculate_success_rate(df)

    # Imprime tabela
    print_summary_table(summary)

    # Gera gráficos
    plot_degradation_curve(
        summary,
        str(output_dir / 'degradation_curve.png')
    )

    plot_classification_distribution(
        df,
        str(output_dir / 'classification_distribution.png')
    )

    print("\nGráficos gerados com sucesso!")


if __name__ == '__main__':
    main()
