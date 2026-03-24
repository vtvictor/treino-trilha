import streamlit as st

workouts = {
    "Quarta (Força)": [
        "Aquecimento (5 min)",
        "Agachamento 4x 8-10",
        "Leg Press 4x 10-12",
        "Afundo 3x 10 cada perna",
        "Mesa Flexora 3x 10-12",
        "Cadeira Extensora 3x 12-15",
        "Panturrilha 4x 12-15",
    ],
    "Sábado (Resistência)": [
        "Esteira inclinada (20 min)",
        "Step 3x 10 cada perna",
        "Afundo 3x 12 cada perna",
        "Leg Press 3x 15-20",
        "Panturrilha 4x 15-20",
        "Prancha 3x 30-45s",
    ],
}

st.title("🏋️ Treino de Trilha")

day = st.selectbox("Escolha o dia:", list(workouts.keys()))

st.write("### Exercícios")

for i, exercise in enumerate(workouts[day]):
    st.checkbox(exercise, key=f"{day}_{i}")