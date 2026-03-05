import random

class FishWeightService:
    """处理鱼类权重计算与期望价值拟合的服务"""
    def __init__(self):
        self.weight_cache = {}

    def _calculate_ev(self, fish_list, weights):
        total_weight = sum(weights)
        if total_weight <= 0:
            return 0
        return sum(f.base_value * w for f, w in zip(fish_list, weights)) / total_weight

    def get_weights(self, fish_list, coins_chance):
        cache_key = (tuple(f.fish_id for f in fish_list), round(coins_chance, 6))
        if cache_key in self.weight_cache:
            return self.weight_cache[cache_key]

        base_weights = [1.0 for _ in fish_list] 
        base_ev = self._calculate_ev(fish_list, base_weights)
        target_ev = base_ev * (1 + coins_chance)
        max_value = max(f.base_value for f in fish_list)

        if target_ev >= max_value:
            final_weights = [1.0 if f.base_value == max_value else 0.0 for f in fish_list]
        else:
            low, high = 0.0, 10.0
            final_weights = base_weights
            for _ in range(50):
                mid = (low + high) / 2.0
                try:
                    temp_weights = [w * ((f.base_value / base_ev) ** mid) for f, w in zip(fish_list, base_weights)]
                except OverflowError:
                    high = mid
                    continue
                    
                current_ev = self._calculate_ev(fish_list, temp_weights)
                if abs(current_ev - target_ev) < 0.01:
                    final_weights = temp_weights
                    break
                
                if current_ev < target_ev:
                    low = mid
                else:
                    high = mid
            else:
                final_weights = temp_weights 

        self.weight_cache[cache_key] = final_weights
        return final_weights

    def choose_fish(self, new_fish_list, coins_chance):
        """替代原来的 get_fish_template 函数"""
        if not new_fish_list:
            return None
        if len(new_fish_list) == 1:
            return new_fish_list[0]

        weights = self.get_weights(new_fish_list, coins_chance)
        return random.choices(new_fish_list, weights=weights, k=1)[0]