
def calculate_damages(overcharges, destruction, emotional_harm):
    return overcharges + destruction + emotional_harm

if __name__ == "__main__":
    print("Total Damages:", calculate_damages(22000, 35000, 10000))
