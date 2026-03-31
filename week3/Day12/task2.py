import numpy as np
from task1 import get_embedding

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

text1 = "如何训练一只猫"
text2 = "猫的训练技巧"
text3 = "量子计算机原理"

v1 = get_embedding(text1)
v2 = get_embedding(text2)
v3 = get_embedding(text3)

print(f"text1 vs text2（语义相近）: {cosine_similarity(v1, v2):.4f}")
print(f"text1 vs text3（语义无关）: {cosine_similarity(v1, v3):.4f}")
