"""
AI strategies for selecting numbers
"""
from game.rules import GameRules
import math
import random


class AIStrategy:
    """Base class for AI strategies"""
    
    def select_number(self, dice_values: list, player_progress: dict) -> int:
        """Select which number to collect based on strategy"""
        raise NotImplementedError


class ProbabilityStrategy(AIStrategy):
    """Strategy: Choose statistically least probable combination (most valuable)"""
    
    @staticmethod
    def binomial_coefficient(n: int, k: int) -> int:
        """Calculate binomial coefficient C(n, k)"""
        if k > n or k < 0:
            return 0
        return math.factorial(n) // (math.factorial(k) * math.factorial(n - k))
    
    @staticmethod
    def calculate_singles_probability(num_dice: int, target_count: int) -> float:
        """
        Calculate probability of getting exactly 'target_count' of a specific number
        in 'num_dice' dice rolls using binomial distribution
        
        P(X = k) = C(n, k) * (1/6)^k * (5/6)^(n-k)
        """
        if target_count == 0:
            return 1.0
        
        n = num_dice
        k = target_count
        p = 1.0 / 6.0  # Probability of getting specific number on one die
        
        coeff = ProbabilityStrategy.binomial_coefficient(n, k)
        probability = coeff * (p ** k) * ((1 - p) ** (n - k))
        
        return probability
    
    @staticmethod
    def calculate_pair_probability(num_dice: int, num_pairs: int) -> float:
        """
        Estimate probability of getting at least 'num_pairs' combinations
        This is a simplified calculation
        """
        # Probability of getting a specific pair (e.g., one specific die showing X and another showing Y)
        # This is an approximation - actual calculation is more complex
        if num_pairs == 0:
            return 1.0
        
        # Probability that at least 2 dice can form one pair
        # Simplified: probability decreases exponentially with more pairs needed
        base_prob = 0.28  # Approximate probability of forming one specific pair
        probability = base_prob ** num_pairs
        
        return probability
    
    def select_number(self, dice_values: list, player_progress: dict) -> int:
        """Select number based on statistical probability (lower = more valuable)"""
        options = {}
        
        # Check all possible numbers 1-12
        for target in range(1, 13):
            # Skip if already completed
            if player_progress.get(target, 0) >= 6:
                continue
            
            singles_count = 0
            pairs_count = 0
            total_probability = 1.0
            
            # Count singles (only for 1-6)
            if target <= 6:
                singles_count = GameRules.count_single_matches(dice_values, target)
                if singles_count > 0:
                    # Calculate probability of getting this many singles
                    singles_prob = self.calculate_singles_probability(6, singles_count)
                    total_probability *= singles_prob
            
            # Count combinations
            pairs = GameRules.find_combinations(dice_values, target)
            pairs_count = len(pairs)
            
            if pairs_count > 0:
                # Calculate probability of getting these pairs
                pairs_prob = self.calculate_pair_probability(6, pairs_count)
                total_probability *= pairs_prob
            
            total_count = singles_count + pairs_count
            
            # ONLY add to options if we can actually make this number with current dice!
            if total_count > 0:
                # Store the inverse of probability (lower probability = higher value)
                # Multiply by total count to prioritize getting more items when probability is similar
                value = (1.0 / total_probability) * total_count
                
                # Add tiebreaker: prefer higher numbers when value is similar
                # because higher sums are generally harder to get (e.g., 12 vs 7)
                # Add small bonus based on distance from 7 (most common sum)
                general_rarity = abs(target - 7) * 0.01  # Small tiebreaker bonus
                value += general_rarity
                
                options[target] = value
        
        if not options:
            # No valid options, pick random incomplete number
            for target in range(1, 13):
                if player_progress.get(target, 0) < 6:
                    return target
            return 1
        
        # Return number with highest value (lowest probability, most rare)
        return max(options, key=options.get)


class CompletionStrategy(AIStrategy):
    """Strategy: Complete numbers quickly to get bonus turns"""
    
    def select_number(self, dice_values: list, player_progress: dict) -> int:
        """Select number closest to completion"""
        options = {}
        
        # Check all possible numbers 1-12
        for target in range(1, 13):
            current = player_progress.get(target, 0)
            
            # Skip if already completed
            if current >= 6:
                continue
            
            count = 0
            # Count singles (only for 1-6)
            if target <= 6:
                count += GameRules.count_single_matches(dice_values, target)
            
            # Count combinations
            pairs = GameRules.find_combinations(dice_values, target)
            count += len(pairs)
            
            if count > 0:
                # Calculate how close to completion
                # Higher score = closer to completion
                remaining = 6 - current
                value = 100 - remaining + count  # Prioritize almost complete
                options[target] = value
        
        if not options:
            # No valid options, pick random incomplete number
            for target in range(1, 13):
                if player_progress.get(target, 0) < 6:
                    return target
            return 1
        
        # Return number closest to completion
        return max(options, key=options.get)


class RandomStrategy(AIStrategy):
    """Strategy: Completely random selection"""
    
    def select_number(self, dice_values: list, player_progress: dict) -> int:
        """Randomly select from available options"""
        options = []
        
        # Check all possible numbers 1-12
        for target in range(1, 13):
            # Skip if already completed
            if player_progress.get(target, 0) >= 6:
                continue
            
            # Check for singles (1-6 only)
            if target <= 6 and target in dice_values:
                options.append(target)
            
            # Check for combinations (7-12)
            if target > 6:
                pairs = GameRules.find_combinations(dice_values, target)
                if len(pairs) > 0:
                    options.append(target)
        
        # Random choice from available options
        if options:
            return random.choice(options)
        
        # Fallback - pick first incomplete number
        for target in range(1, 13):
            if player_progress.get(target, 0) < 6:
                return target
        return 1

