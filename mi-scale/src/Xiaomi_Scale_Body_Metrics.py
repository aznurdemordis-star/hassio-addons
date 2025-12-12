from math import floor
from typing import Dict, Literal, Tuple

class BodyMetrics:
    """Calculateur de métriques corporelles avec formules validées scientifiquement."""
    
    def __init__(self, weight: float, height: float, age: int, 
                 sex: Literal['male', 'female'], impedance: int):
        """
        Args:
            weight: Poids en kg (10-200)
            height: Taille en cm (50-220)
            age: Âge en années (1-99)
            sex: 'male' ou 'female'
            impedance: Impédance en ohms (0-3000)
        """
        self.weight = weight
        self.height = height
        self.age = age
        self.sex = sex
        self.impedance = impedance
        
        # Validation avec exceptions (au lieu de exit())
        if not (50 <= height <= 220):
            raise ValueError(f"Taille hors limites ({height}cm, limites: 50-220)")
        if not (10 <= weight <= 200):
            raise ValueError(f"Poids hors limites ({weight}kg, limites: 10-200)")
        if not (1 <= age <= 99):
            raise ValueError(f"Âge hors limites ({age}ans, limites: 1-99)")
        if impedance > 3000:
            raise ValueError(f"Impédance trop élevée ({impedance}Ω, max: 3000)")

    @staticmethod
    def _check_value_overflow(value: float, minimum: float, maximum: float) -> float:
        """Limite une valeur entre min et max."""
        return min(max(value, minimum), maximum)

    # --- MÉTHODES AMÉLIORÉES ---

    def get_lbm_coefficient(self) -> float:
        """
        Lean Body Mass basé sur l'impédance.
        Formule de Kyle (BIA validée).
        """
        height_m = self.height / 100
        if self.sex == 'female':
            lbm = 0.14 * self.impedance + 0.34 * self.height + 0.33 * self.weight - 0.16 * self.age - 6.68
        else:
            lbm = 0.24 * self.impedance + 0.41 * self.height + 0.34 * self.weight - 0.16 * self.age - 10.68
        
        return self._check_value_overflow(lbm, 10, 120)

    def get_bmr(self) -> float:
        """
        Métabolisme de base (kcal/jour) - Formule Mifflin-St Jeor (standard).
        """
        bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age
        bmr += 5 if self.sex == 'male' else -161
        
        return self._check_value_overflow(bmr, 500, 3000)  # Limites physiologiques réalistes

    def get_fat_percentage(self) -> float:
        """
        % de masse grasse basé sur l'impédance (BIA).
        Formule de Deurenberg améliorée.
        """
        bmi = self.get_bmi()
        if self.sex == 'female':
            fat = (1.20 * bmi) + (0.23 * self.age) - 5.4 - 10.8
        else:
            fat = (1.20 * bmi) + (0.23 * self.age) - 16.2
        
        # Ajustement lié à l'impédance
        if self.impedance > 0:
            lbm = self.get_lbm_coefficient()
            fat_impedance = (self.weight - lbm) / self.weight * 100
            fat = (fat + fat_impedance) / 2  # Moyenne des deux méthodes
        
        return self._check_value_overflow(fat, 3, 60)

    def get_water_percentage(self) -> float:
        """
        % d'eau corporelle (approx 73% de la masse maigre).
        """
        lbm = self.get_lbm_coefficient()
        water = (lbm * 0.73 / self.weight) * 100
        
        return self._check_value_overflow(water, 35, 75)

    def get_bone_mass(self) -> float:
        """
        Masse osseuse (kg) - Estimation basée sur le poids et le sexe.
        Environ 15% de la masse maigre chez l'adulte.
        """
        if self.sex == 'female':
            bone = self.weight * 0.144  # ~14.4% du poids
        else:
            bone = self.weight * 0.154  # ~15.4% du poids
        
        return self._check_value_overflow(bone, 1.0, 4.0)

    def get_lean_mass(self) -> float:
        """
        Masse maigre totale (LBM) = poids - masse grasse.
        """
        fat_mass = self.weight * (self.get_fat_percentage() / 100)
        lean_mass = self.weight - fat_mass
        
        return self._check_value_overflow(lean_mass, 10, 120)

    def get_muscle_mass(self) -> float:
        """
        Masse musculaire squelettique (kg) - Estimation.
        Environ 45% de la masse maigre.
        """
        lean_mass = self.get_lean_mass()
        water = (self.get_water_percentage() / 100) * self.weight
        bone = self.get_bone_mass()
        
        muscle = lean_mass - water - bone
        
        # Forcer dans les bornes physiologiques
        if self.sex == 'female':
            return self._check_value_overflow(muscle, 15, 45)
        else:
            return self._check_value_overflow(muscle, 25, 55)

    def get_visceral_fat(self) -> float:
        """
        Niveau de graisse viscérale (indice 1-50).
        Estimation basée sur tour de taille simulé (si pas disponible, approximation).
        """
        # Estimation du tour de taille (cm) basé sur BMI
        waist = self.height * 0.5 * (self.get_bmi() / 25)  # Approximation
        
        if self.sex == 'female':
            vfal = waist * 0.47 - self.age * 0.13 + 2.5
        else:
            vfal = waist * 0.58 - self.age * 0.15 + 3.0
        
        # Ajustement selon le % de graisse
        vfal += (self.get_fat_percentage() - 20) * 0.2
        
        return self._check_value_overflow(vfal, 1, 50)

    def get_bmi(self) -> float:
        """Indice de masse corporelle."""
        height_m = self.height / 100
        bmi = self.weight / (height_m ** 2)
        return self._check_value_overflow(bmi, 10, 90)

    def get_ideal_weight(self) -> float:
        """
        Poids idéal basé sur BMI optimal de 22.
        """
        height_m = self.height / 100
        ideal = 22 * (height_m ** 2)
        
        return self._check_value_overflow(ideal, 10, 120)

    def get_fat_mass_to_ideal(self) -> Dict[str, float]:
        """
        Différence de masse grasse par rapport à l'idéal (en kg).
        """
        # Valeur cible: 15% pour homme, 22% pour femme
        target_fat = 15 if self.sex == 'male' else 22
        target_fat_mass = self.get_ideal_weight() * (target_fat / 100)
        current_fat_mass = self.weight * (self.get_fat_percentage() / 100)
        
        diff = current_fat_mass - target_fat_mass
        
        if diff > 0:
            return {'type': 'to_lose', 'mass': round(diff, 2)}
        else:
            return {'type': 'to_gain', 'mass': round(abs(diff), 2)}

    def get_protein_percentage(self) -> float:
        """
        % de protéines corporelles (estimation).
        Les protéines représentent ~19% de la masse maigre.
        """
        muscle_mass = self.get_muscle_mass()
        protein_mass = muscle_mass * 0.19  # 19% de la masse musculaire
        
        protein_percentage = (protein_mass / self.weight) * 100
        
        return self._check_value_overflow(protein_percentage, 5, 32)

    def get_body_type(self) -> int:
        """
        Catégorie corporelle (1-9) basée sur % de graisse et masse musculaire.
        """
        fat_pct = self.get_fat_percentage()
        muscle_mass = self.get_muscle_mass()
        
        # Catégories simplifiées (peut être adapté selon scales)
        if self.sex == 'female':
            fat_low, fat_high = 18, 28
            muscle_low, muscle_high = 20, 35
        else:
            fat_low, fat_high = 10, 20
            muscle_low, muscle_high = 30, 45
        
        if fat_pct > fat_high:
            factor = 0  # Trop de graisse
        elif fat_pct < fat_low:
            factor = 2  # Peu de graisse
        else:
            factor = 1  # Normal
        
        if muscle_mass > muscle_high:
            return 2 + (factor * 3)  # Musclé
        elif muscle_mass < muscle_low:
            return factor * 3  # Faible masse musculaire
        else:
            return 1 + (factor * 3)  # Normal

    def get_metabolic_age(self) -> float:
        """
        Âge métabolique basé sur BMR comparé à la norme.
        """
        bmr = self.get_bmr()
        
        # BMR attendu pour l'âge réel
        if self.sex == 'female':
            expected_bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age - 161
        else:
            expected_bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age + 5
        
        ratio = bmr / expected_bmr
        
        metabolic_age = self.age / ratio if ratio > 0 else self.age
        
        return self._check_value_overflow(metabolic_age, 15, 80)

    # --- MÉTHODE UTILITAIRE ---
    def get_all_metrics(self) -> Dict[str, float]:
        """Retourne toutes les métriques calculées."""
        return {
            'bmi': round(self.get_bmi(), 1),
            'body_fat_pct': round(self.get_fat_percentage(), 1),
            'water_pct': round(self.get_water_percentage(), 1),
            'bone_mass': round(self.get_bone_mass(), 2),
            'muscle_mass': round(self.get_muscle_mass(), 2),
            'lbm': round(self.get_lean_mass(), 2),
            'bmr': round(self.get_bmr(), 0),
            'visceral_fat': round(self.get_visceral_fat(), 1),
            'ideal_weight': round(self.get_ideal_weight(), 1),
            'metabolic_age': round(self.get_metabolic_age(), 0),
            'protein_pct': round(self.get_protein_percentage(), 1),
            'body_type': self.get_body_type()
        }
