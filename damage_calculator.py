from typing import List, Callable
import math # For math.isclose or abs for assertions

def calculate_outgoing_damage(
    skill_multiplier: float,
    scaling_attribute_value: float,
    extra_multiplier: float,
    extra_dmg: float,
    elemental_dmg_bonus_percent: float,
    all_type_dmg_bonus_percent: float,
    dot_dmg_bonus_percent: float,
    other_dmg_bonus_percent: float,
    attacker_level: int,
    enemy_base_def: float,
    enemy_def_percent_buffs_debuffs: float,
    def_reduction_percent: float,
    def_ignore_percent: float,
    enemy_current_res_percent: float,
    res_pen_percent: float,
    elemental_dmg_taken_bonus_percent: float,
    all_type_dmg_taken_bonus_percent: float,
    universal_dmg_reduction_sources: List[float],
    weaken_percent: float,
) -> float:
    """
    Calculates the final outgoing damage based on various combat parameters.

    Args:
        skill_multiplier: The skill's damage multiplier (e.g., 0.6 for 60%).
        scaling_attribute_value: The value of the character's scaling attribute (ATK, HP, or DEF).
        extra_multiplier: An additional damage multiplier (e.g., 0.2 for 20%).
        extra_dmg: A flat amount of extra damage.
        elemental_dmg_bonus_percent: Elemental damage bonus percentage (e.g., 0.258 for 25.8%).
        all_type_dmg_bonus_percent: All type damage bonus percentage (e.g., 0.1 for 10%).
        dot_dmg_bonus_percent: Damage over time (DoT) bonus percentage (e.g., 0.12 for 12%).
        other_dmg_bonus_percent: Other miscellaneous damage bonus percentage.
        attacker_level: The attacker's character level.
        enemy_base_def: The enemy's base defense value.
        enemy_def_percent_buffs_debuffs: Enemy DEF percentage buffs or debuffs (e.g., 0.2 for 20% buff, -0.1 for 10% debuff).
        def_reduction_percent: Defense reduction percentage (e.g., 0.15 for 15%).
        def_ignore_percent: Defense ignore percentage (e.g., 0.2 for 20%).
        enemy_current_res_percent: Enemy's current resistance percentage (e.g., 0.2 for 20%).
        res_pen_percent: Resistance penetration percentage (e.g., 0.1 for 10%).
        elemental_dmg_taken_bonus_percent: Elemental damage taken bonus percentage (e.g., 0.1 for 10%).
        all_type_dmg_taken_bonus_percent: All type damage taken bonus percentage (e.g., 0.05 for 5%).
        universal_dmg_reduction_sources: A list of universal damage reduction sources (e.g., [0.1, 0.05] for 10% and 5% reduction).
        weaken_percent: Weaken percentage (e.g., 0.15 for 15%).

    Returns:
        The final calculated outgoing damage.
    """

    # 1. Base_DMG
    base_dmg = (skill_multiplier + extra_multiplier) * scaling_attribute_value + extra_dmg

    # 2. DMG_Percent_Multiplier
    dmg_percent_multiplier = (
        1
        + elemental_dmg_bonus_percent
        + all_type_dmg_bonus_percent
        + dot_dmg_bonus_percent
        + other_dmg_bonus_percent
    )

    # 3. Enemy_Final_DEF
    enemy_final_def = enemy_base_def * (
        1 + enemy_def_percent_buffs_debuffs - (def_reduction_percent + def_ignore_percent)
    )
    enemy_final_def = max(0, enemy_final_def)  # DEF cannot go below 0

    # 4. DEF_Multiplier
    # Using Prydwen formula: DEF Multiplier = 1 - [Enemy_Final_DEF / (Enemy_Final_DEF + 200 + 10 * Attacker_Level)]
    def_multiplier_denominator = enemy_final_def + 200 + (10 * attacker_level)
    if def_multiplier_denominator == 0: # Avoid division by zero, though unlikely with 200 + 10 * Attacker_Level
        def_multiplier = 1
    else:
        def_multiplier = 1 - (enemy_final_def / def_multiplier_denominator)


    # 5. RES_Multiplier
    # (Enemy_Current_RES_Percent - RES_PEN_Percent) should be clamped between -1.0 and 0.9.
    # Then RES_Multiplier = 1 - clamped_value.
    effective_res = enemy_current_res_percent - res_pen_percent
    clamped_effective_res = max(-1.0, min(0.9, effective_res))
    res_multiplier = 1 - clamped_effective_res

    # 6. DMG_Taken_Multiplier
    dmg_taken_multiplier = (
        1 + elemental_dmg_taken_bonus_percent + all_type_dmg_taken_bonus_percent
    )

    # 7. Universal_DMG_Reduction_Multiplier
    universal_dmg_reduction_multiplier = 1.0
    for reduction_source in universal_dmg_reduction_sources:
        universal_dmg_reduction_multiplier *= (1 - reduction_source)

    # 8. Weaken_Multiplier
    weaken_multiplier = 1 - weaken_percent

    # Final Outgoing DMG Calculation
    outgoing_dmg = (
        base_dmg
        * dmg_percent_multiplier
        * def_multiplier
        * res_multiplier
        * dmg_taken_multiplier
        * universal_dmg_reduction_multiplier
        * weaken_multiplier
    )

    return outgoing_dmg

def calculate_total_atk(char_base_atk: float, lc_base_atk: float, atk_percent_bonus: float, flat_atk_bonus: float) -> float:
    """
    Calculates the total Attack (ATK) of a character.

    Formula: Total_ATK = (Character_Base_ATK + LC_Base_ATK) * (1 + ATK_Percent_Bonus) + Flat_ATK_Bonus

    Args:
        char_base_atk: The character's base ATK.
        lc_base_atk: The base ATK from the equipped Light Cone.
        atk_percent_bonus: The sum of all percentage ATK bonuses (e.g., 0.48 for 48%).
        flat_atk_bonus: The sum of all flat ATK bonuses.

    Returns:
        The total calculated ATK value.
    """
    total_atk = (char_base_atk + lc_base_atk) * (1 + atk_percent_bonus) + flat_atk_bonus
    return total_atk

def calculate_total_hp(char_base_hp: float, lc_base_hp: float, hp_percent_bonus: float, flat_hp_bonus: float) -> float:
    """
    Calculates the total Health Points (HP) of a character.

    Formula: Total_HP = (Character_Base_HP + LC_Base_HP) * (1 + HP_Percent_Bonus) + Flat_HP_Bonus

    Args:
        char_base_hp: The character's base HP.
        lc_base_hp: The base HP from the equipped Light Cone.
        hp_percent_bonus: The sum of all percentage HP bonuses (e.g., 0.48 for 48%).
        flat_hp_bonus: The sum of all flat HP bonuses.

    Returns:
        The total calculated HP value.
    """
    total_hp = (char_base_hp + lc_base_hp) * (1 + hp_percent_bonus) + flat_hp_bonus
    return total_hp

def calculate_total_def(char_base_def: float, lc_base_def: float, def_percent_bonus: float, flat_def_bonus: float) -> float:
    """
    Calculates the total Defense (DEF) of a character.

    Formula: Total_DEF = (Character_Base_DEF + LC_Base_DEF) * (1 + DEF_Percent_Bonus) + Flat_DEF_Bonus

    Args:
        char_base_def: The character's base DEF.
        lc_base_def: The base DEF from the equipped Light Cone.
        def_percent_bonus: The sum of all percentage DEF bonuses (e.g., 0.48 for 48%).
        flat_def_bonus: The sum of all flat DEF bonuses.

    Returns:
        The total calculated DEF value.
    """
    total_def = (char_base_def + lc_base_def) * (1 + def_percent_bonus) + flat_def_bonus
    return total_def

def get_float_input(prompt: str, default: float = None) -> float:
    while True:
        try:
            user_input = input(prompt)
            if default is not None and not user_input:
                return default
            return float(user_input)
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_int_input(prompt: str, default: int = None) -> int:
    while True:
        try:
            user_input = input(prompt)
            if default is not None and not user_input:
                return default
            return int(user_input)
        except ValueError:
            print("Invalid input. Please enter an integer.")

def get_list_float_input(prompt: str, default_str: str = "0.1") -> List[float]:
    while True:
        try:
            user_input = input(prompt)
            if not user_input and default_str is not None:
                user_input = default_str
            
            if not user_input: # Handles case where default_str is None or empty
                 return []

            return [float(item.strip()) for item in user_input.split(',')]
        except ValueError:
            print("Invalid input. Please enter a comma-separated list of numbers (e.g., 0.1,0.05).")

def run_prydwen_examples():
    """
    Runs example damage calculations based on Prydwen.gg article and asserts results.
    """
    print("\n" + "="*30)
    print("Running Prydwen.gg Examples")
    print("="*30)
    tolerance = 1.0 # Allow for small rounding differences

    # Common parameters for Tingyun Lvl 50 vs Enemy Lvl 50 (derived Enemy_Final_DEF = 700)
    tingyun_attacker_level = 50
    tingyun_atk = 1062
    tingyun_skill_multiplier = 0.6
    tingyun_lightning_dmg_bonus = 0.258
    tingyun_basic_dmg_bonus_musketeer = 0.1 # other_dmg_bonus_percent
    
    enemy_base_def_lvl50_vs_lvl50_eff_def_mult_50_percent = 700.0

    # --- Tingyun Example 1: Enemy not broken, not weak to Lightning ---
    # Expected DMG: 312
    print("\n--- Tingyun Example 1: Enemy not broken, not weak to Lightning ---")
    ty_ex1_calculated_dmg = calculate_outgoing_damage(
        skill_multiplier=tingyun_skill_multiplier,
        scaling_attribute_value=tingyun_atk,
        extra_multiplier=0.0,
        extra_dmg=0.0,
        elemental_dmg_bonus_percent=tingyun_lightning_dmg_bonus,
        all_type_dmg_bonus_percent=0.0,
        dot_dmg_bonus_percent=0.0,
        other_dmg_bonus_percent=tingyun_basic_dmg_bonus_musketeer,
        attacker_level=tingyun_attacker_level,
        enemy_base_def=enemy_base_def_lvl50_vs_lvl50_eff_def_mult_50_percent,
        enemy_def_percent_buffs_debuffs=0.0,
        def_reduction_percent=0.0,
        def_ignore_percent=0.0,
        enemy_current_res_percent=0.2, # Results in 80% RES Multiplier
        res_pen_percent=0.0,
        elemental_dmg_taken_bonus_percent=0.0,
        all_type_dmg_taken_bonus_percent=0.0,
        universal_dmg_reduction_sources=[0.1], # 90% Toughness Multiplier
        weaken_percent=0.0,
    )
    ty_ex1_expected_dmg = 312
    print(f"Calculated Damage: {ty_ex1_calculated_dmg:.2f}")
    print(f"Expected Damage: {ty_ex1_expected_dmg}")
    if abs(ty_ex1_calculated_dmg - ty_ex1_expected_dmg) < tolerance:
        print("Test Passed")
    else:
        print(f"Test Failed. Difference: {abs(ty_ex1_calculated_dmg - ty_ex1_expected_dmg):.2f}")

    # --- Tingyun Example 2: Enemy broken ---
    # Expected DMG: 346
    print("\n--- Tingyun Example 2: Enemy broken ---")
    ty_ex2_calculated_dmg = calculate_outgoing_damage(
        skill_multiplier=tingyun_skill_multiplier,
        scaling_attribute_value=tingyun_atk,
        extra_multiplier=0.0,
        extra_dmg=0.0,
        elemental_dmg_bonus_percent=tingyun_lightning_dmg_bonus,
        all_type_dmg_bonus_percent=0.0,
        dot_dmg_bonus_percent=0.0,
        other_dmg_bonus_percent=tingyun_basic_dmg_bonus_musketeer,
        attacker_level=tingyun_attacker_level,
        enemy_base_def=enemy_base_def_lvl50_vs_lvl50_eff_def_mult_50_percent,
        enemy_def_percent_buffs_debuffs=0.0,
        def_reduction_percent=0.0,
        def_ignore_percent=0.0,
        enemy_current_res_percent=0.2, # Not weak to lightning
        res_pen_percent=0.0,
        elemental_dmg_taken_bonus_percent=0.0,
        all_type_dmg_taken_bonus_percent=0.0,
        universal_dmg_reduction_sources=[], # Broken, so 100% Toughness Multiplier
        weaken_percent=0.0,
    )
    ty_ex2_expected_dmg = 346
    print(f"Calculated Damage: {ty_ex2_calculated_dmg:.2f}")
    print(f"Expected Damage: {ty_ex2_expected_dmg}")
    if abs(ty_ex2_calculated_dmg - ty_ex2_expected_dmg) < tolerance:
        print("Test Passed")
    else:
        print(f"Test Failed. Difference: {abs(ty_ex2_calculated_dmg - ty_ex2_expected_dmg):.2f}")

    # --- Tingyun Example 3: Enemy weak to Lightning, not broken ---
    # Expected DMG: 389
    print("\n--- Tingyun Example 3: Enemy weak to Lightning, not broken ---")
    ty_ex3_calculated_dmg = calculate_outgoing_damage(
        skill_multiplier=tingyun_skill_multiplier,
        scaling_attribute_value=tingyun_atk,
        extra_multiplier=0.0,
        extra_dmg=0.0,
        elemental_dmg_bonus_percent=tingyun_lightning_dmg_bonus,
        all_type_dmg_bonus_percent=0.0,
        dot_dmg_bonus_percent=0.0,
        other_dmg_bonus_percent=tingyun_basic_dmg_bonus_musketeer,
        attacker_level=tingyun_attacker_level,
        enemy_base_def=enemy_base_def_lvl50_vs_lvl50_eff_def_mult_50_percent,
        enemy_def_percent_buffs_debuffs=0.0,
        def_reduction_percent=0.0,
        def_ignore_percent=0.0,
        enemy_current_res_percent=0.0, # Weak to Lightning, 100% RES Multiplier
        res_pen_percent=0.0,
        elemental_dmg_taken_bonus_percent=0.0,
        all_type_dmg_taken_bonus_percent=0.0,
        universal_dmg_reduction_sources=[0.1], # Not broken
        weaken_percent=0.0,
    )
    ty_ex3_expected_dmg = 389
    print(f"Calculated Damage: {ty_ex3_calculated_dmg:.2f}")
    print(f"Expected Damage: {ty_ex3_expected_dmg}")
    # Prydwen got 389.4, so math.isclose is better here or a slightly higher tolerance
    if math.isclose(ty_ex3_calculated_dmg, ty_ex3_expected_dmg, abs_tol=tolerance):
        print("Test Passed")
    else:
        print(f"Test Failed. Difference: {abs(ty_ex3_calculated_dmg - ty_ex3_expected_dmg):.2f}")


    # Common parameters for Qingque Lvl 50 vs Enemy Lvl 50 (derived Enemy_Final_DEF = 700)
    qingque_attacker_level = 50
    qingque_atk = 1432
    qingque_skill_multiplier = 0.7
    qingque_quantum_dmg_bonus = 0.186
    qingque_last_tile_buff = 0.15 # all_type_dmg_bonus_percent
    qingque_basic_dmg_bonus_musketeer = 0.1 # other_dmg_bonus_percent

    # --- Qingque Example 1: Enemy not broken, not weak to Quantum ---
    # Expected DMG: 518
    print("\n--- Qingque Example 1: Enemy not broken, not weak to Quantum ---")
    qq_ex1_calculated_dmg = calculate_outgoing_damage(
        skill_multiplier=qingque_skill_multiplier,
        scaling_attribute_value=qingque_atk,
        extra_multiplier=0.0,
        extra_dmg=0.0,
        elemental_dmg_bonus_percent=qingque_quantum_dmg_bonus,
        all_type_dmg_bonus_percent=qingque_last_tile_buff,
        dot_dmg_bonus_percent=0.0,
        other_dmg_bonus_percent=qingque_basic_dmg_bonus_musketeer,
        attacker_level=qingque_attacker_level,
        enemy_base_def=enemy_base_def_lvl50_vs_lvl50_eff_def_mult_50_percent,
        enemy_def_percent_buffs_debuffs=0.0,
        def_reduction_percent=0.0,
        def_ignore_percent=0.0,
        enemy_current_res_percent=0.2, # Not weak to Quantum
        res_pen_percent=0.0,
        elemental_dmg_taken_bonus_percent=0.0,
        all_type_dmg_taken_bonus_percent=0.0,
        universal_dmg_reduction_sources=[0.1], # Not broken
        weaken_percent=0.0,
    )
    qq_ex1_expected_dmg = 518
    print(f"Calculated Damage: {qq_ex1_calculated_dmg:.2f}")
    print(f"Expected Damage: {qq_ex1_expected_dmg}")
    if abs(qq_ex1_calculated_dmg - qq_ex1_expected_dmg) < tolerance:
        print("Test Passed")
    else:
        print(f"Test Failed. Difference: {abs(qq_ex1_calculated_dmg - qq_ex1_expected_dmg):.2f}")

    # --- Qingque Example 2: Enemy weak to Quantum, not broken ---
    # Expected DMG: 648 (Prydwen got 647.8)
    print("\n--- Qingque Example 2: Enemy weak to Quantum, not broken ---")
    qq_ex2_calculated_dmg = calculate_outgoing_damage(
        skill_multiplier=qingque_skill_multiplier,
        scaling_attribute_value=qingque_atk,
        extra_multiplier=0.0,
        extra_dmg=0.0,
        elemental_dmg_bonus_percent=qingque_quantum_dmg_bonus,
        all_type_dmg_bonus_percent=qingque_last_tile_buff,
        dot_dmg_bonus_percent=0.0,
        other_dmg_bonus_percent=qingque_basic_dmg_bonus_musketeer,
        attacker_level=qingque_attacker_level,
        enemy_base_def=enemy_base_def_lvl50_vs_lvl50_eff_def_mult_50_percent,
        enemy_def_percent_buffs_debuffs=0.0,
        def_reduction_percent=0.0,
        def_ignore_percent=0.0,
        enemy_current_res_percent=0.0, # Weak to Quantum
        res_pen_percent=0.0,
        elemental_dmg_taken_bonus_percent=0.0,
        all_type_dmg_taken_bonus_percent=0.0,
        universal_dmg_reduction_sources=[0.1], # Not broken
        weaken_percent=0.0,
    )
    qq_ex2_expected_dmg = 648 # Prydwen 647.8
    print(f"Calculated Damage: {qq_ex2_calculated_dmg:.2f}")
    print(f"Expected Damage: {qq_ex2_expected_dmg} (Prydwen: 647.8)")
    if math.isclose(qq_ex2_calculated_dmg, qq_ex2_expected_dmg, abs_tol=tolerance):
        print("Test Passed")
    else:
        print(f"Test Failed. Difference: {abs(qq_ex2_calculated_dmg - qq_ex2_expected_dmg):.2f}")
    
    print("\n" + "="*30)
    print("Prydwen Examples Complete")
    print("="*30 + "\n")


if __name__ == "__main__":
    print("Welcome to the Damage Calculator CLI!")
    
    scaling_attribute_value = 0.0

    # 1. Optional Stat Calculation
    # Check if sys.stdin.isatty() to see if it's an interactive session
    import sys
    run_cli_interaction = True
    if not sys.stdin.isatty(): # If not interactive (e.g. piped input or just running script)
        # Check if any command line arguments were passed to potentially bypass CLI
        # For now, we'll assume if not interactive, maybe skip direct CLI interaction
        # or have a specific flag to run tests. For this setup, let's assume
        # if not interactive, it might be a test runner, so don't prompt.
        # However, the current request is to run examples *after* CLI.
        # A simple way is to check if there are any args; if "test" is an arg, skip CLI.
        if "test" in sys.argv or "run_examples" in sys.argv:
             print("Test mode detected, skipping interactive CLI.")
             run_cli_interaction = False
    
    if run_cli_interaction:
        calculate_stat_first_choice = input("Do you want to calculate a character's ATK, HP, or DEF first? (yes/no, default: no): ").strip().lower()
        if calculate_stat_first_choice == 'yes':
            stat_type_choice = ""
            while stat_type_choice not in ['atk', 'hp', 'def']:
                stat_type_choice = input("Which stat do you want to calculate? (atk/hp/def): ").strip().lower()
                if stat_type_choice not in ['atk', 'hp', 'def']:
                    print("Invalid stat type. Please choose 'atk', 'hp', or 'def'.")

            char_base_stat = get_float_input(f"Enter Character Base {stat_type_choice.upper()}: ")
            lc_base_stat = get_float_input(f"Enter Light Cone Base {stat_type_choice.upper()}: ")
            stat_percent_bonus = get_float_input(f"Enter Total {stat_type_choice.upper()} Percent Bonus (e.g., 0.48 for 48%): ")
            flat_stat_bonus = get_float_input(f"Enter Total Flat {stat_type_choice.upper()} Bonus: ")

            if stat_type_choice == 'atk':
                scaling_attribute_value = calculate_total_atk(char_base_stat, lc_base_stat, stat_percent_bonus, flat_stat_bonus)
            elif stat_type_choice == 'hp':
                scaling_attribute_value = calculate_total_hp(char_base_stat, lc_base_stat, stat_percent_bonus, flat_stat_bonus)
            elif stat_type_choice == 'def':
                scaling_attribute_value = calculate_total_def(char_base_stat, lc_base_stat, stat_percent_bonus, flat_stat_bonus)
            
            print(f"Calculated Total {stat_type_choice.upper()}: {scaling_attribute_value:.2f}")
            print("-" * 30)

        # 2. Damage Calculation Inputs
        print("\nEnter parameters for Outgoing Damage Calculation:")

        if scaling_attribute_value == 0.0: # If not calculated above
            scaling_attribute_value = get_float_input("Enter Scaling Attribute Value (ATK, HP, or DEF): ")
        
        skill_multiplier = get_float_input("Enter Skill Multiplier (e.g., 0.6 for 60%): ")
        extra_multiplier = get_float_input("Enter Extra Multiplier (e.g., 0.2 for 20%, default: 0): ", 0.0)
        extra_dmg = get_float_input("Enter Flat Extra Damage (default: 0): ", 0.0)
        elemental_dmg_bonus_percent = get_float_input("Enter Elemental DMG Bonus Percent (e.g., 0.389 for 38.9%): ")
        all_type_dmg_bonus_percent = get_float_input("Enter All-Type DMG Bonus Percent (default: 0): ", 0.0)
        dot_dmg_bonus_percent = get_float_input("Enter DoT DMG Bonus Percent (default: 0): ", 0.0)
        other_dmg_bonus_percent = get_float_input("Enter Other DMG Bonus Percent (e.g., Basic ATK Bonus, default: 0): ", 0.0)
        
        attacker_level = get_int_input("Enter Attacker Level: ")
        enemy_base_def = get_float_input("Enter Enemy Base DEF: ")
        enemy_def_percent_buffs_debuffs = get_float_input("Enter Enemy DEF Percent Buffs/Debuffs (e.g., 0.2 for buff, -0.1 for debuff, default: 0): ", 0.0)
        def_reduction_percent = get_float_input("Enter DEF Reduction Percent (e.g., Pela ult, default: 0): ", 0.0)
        def_ignore_percent = get_float_input("Enter DEF Ignore Percent (e.g., Seele E2, default: 0): ", 0.0)
        
        enemy_current_res_percent = get_float_input("Enter Enemy Current RES Percent (e.g., 0.2 for neutral, 0 for weakness, 0.4 for resistance): ")
        res_pen_percent = get_float_input("Enter RES Penetration Percent (default: 0): ", 0.0)
        
        elemental_dmg_taken_bonus_percent = get_float_input("Enter Elemental DMG Taken Bonus Percent (e.g., Welt ult, default: 0): ", 0.0)
        all_type_dmg_taken_bonus_percent = get_float_input("Enter All-Type DMG Taken Bonus Percent (default: 0): ", 0.0)
        
        universal_dmg_reduction_sources_str = "0.1" # Default for enemy toughness
        universal_dmg_reduction_sources = get_list_float_input(
            f"Enter Universal DMG Reduction Sources (comma-separated floats, e.g., '0.1,0.05', default: '{universal_dmg_reduction_sources_str}' for enemy toughness): ",
            default_str=universal_dmg_reduction_sources_str
        )

        weaken_percent = get_float_input("Enter Weaken Percent (e.g., 0.15 for 15%, default: 0): ", 0.0)

        # 3. Perform Calculation and Display Output
        final_damage = calculate_outgoing_damage(
            skill_multiplier=skill_multiplier,
            scaling_attribute_value=scaling_attribute_value,
            extra_multiplier=extra_multiplier,
            extra_dmg=extra_dmg,
            elemental_dmg_bonus_percent=elemental_dmg_bonus_percent,
            all_type_dmg_bonus_percent=all_type_dmg_bonus_percent,
            dot_dmg_bonus_percent=dot_dmg_bonus_percent,
            other_dmg_bonus_percent=other_dmg_bonus_percent,
            attacker_level=attacker_level,
            enemy_base_def=enemy_base_def,
            enemy_def_percent_buffs_debuffs=enemy_def_percent_buffs_debuffs,
            def_reduction_percent=def_reduction_percent,
            def_ignore_percent=def_ignore_percent,
            enemy_current_res_percent=enemy_current_res_percent,
            res_pen_percent=res_pen_percent,
            elemental_dmg_taken_bonus_percent=elemental_dmg_taken_bonus_percent,
            all_type_dmg_taken_bonus_percent=all_type_dmg_taken_bonus_percent,
            universal_dmg_reduction_sources=universal_dmg_reduction_sources,
            weaken_percent=weaken_percent,
        )

        print("-" * 30)
        print(f"Calculated Outgoing Damage: {final_damage:.2f}")
        print("-" * 30)
        print("Thank you for using the Damage Calculator!")
    
    # Always run Prydwen examples after CLI interaction (if any)
    run_prydwen_examples()
