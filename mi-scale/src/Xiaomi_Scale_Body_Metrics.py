from math import floor
import sys
from body_scales import bodyScales

class bodyMetrics:
    def __init__(self, weight, height, age, sex, impedance):
        self.weight = weight
        self.height = height
        self.age = age
        self.sex = sex
        self.impedance = impedance
        self.scales = bodyScales(age, height, sex, weight)

        # Check for potential out of boundaries
        if self.height > 220:
            print("Height is too high (limit: >220cm) or scale is sleeping")
            sys.stderr.write('Height is over 220cm\n')
            exit()
        elif weight < 10 or weight > 200:
            print("Weight is either too low or too high (limits: <10kg and >200kg)")
            sys.stderr.write('Weight is below 10kg or above 200kg\n')
            exit()
        elif age > 99:
            print("Age is too high (limit >99 years)")
            sys.stderr.write('Age is above 99 years\n')
            exit()
        elif impedance > 3000:
            print("Impedance is above 3000 Ohm")
            sys.stderr.write('Impedance is above 3000 Ohm\n')
            exit()

    def checkValueOverflow(self, value, minimum, maximum):
        if value < minimum:
            return minimum
        elif value > maximum:
            return maximum
        else:
            return value

    # Get LBM coefficient (with impedance) - corrected formula (James formula)
    def getLBMCoefficient(self):
        if self.sex == 'female':
            lbm = (0.29569 * self.weight) + (0.41813 * self.height) - 43.2933
        else:
            lbm = (0.407 * self.weight) + (0.267 * self.height) - 19.2
        lbm -= self.impedance * 0.0068  # keep impedance adjustment
        lbm -= self.age * 0.0542
        return lbm

    # Get BMR - Mifflin-St Jeor formula
    def getBMR(self):
        if self.sex == 'female':
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age - 161
        else:
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age + 5

        return self.checkValueOverflow(bmr, 500, 10000)

    # Get fat percentage - using a common LBM-based formula
    def getFatPercentage(self):
        if self.sex == 'female' and self.age <= 49:
            const = 9.25
        elif self.sex == 'female' and self.age > 49:
            const = 7.25
        else:
            const = 0.8

        LBM = self.getLBMCoefficient()

        # simplified coefficient
        coefficient = 1.0
        fatPercentage = (1.0 - ((LBM - const) / self.weight)) * 100

        return self.checkValueOverflow(fatPercentage, 5, 75)

    # Get water percentage - more standard estimation
    def getWaterPercentage(self):
        waterPercentage = 100 - self.getFatPercentage()
        waterPercentage *= 0.73  # average water proportion
        return self.checkValueOverflow(waterPercentage, 35, 75)

    # Get bone mass - simplified and more realistic
    def getBoneMass(self):
        if self.sex == 'female':
            base = 2.3
        else:
            base = 3.0
        boneMass = base + (self.height / 100) * 0.2
        return self.checkValueOverflow(boneMass, 0.5, 8)

    # Get muscle mass
    def getMuscleMass(self):
        muscleMass = self.weight - ((self.getFatPercentage() * 0.01) * self.weight) - self.getBoneMass()
        return self.checkValueOverflow(muscleMass, 10, 120)

    # Get Visceral Fat - simplified, more linear approximation
    def getVisceralFat(self):
        height_m = self.height / 100
        bmi = self.weight / (height_m ** 2)

        if self.sex == 'male':
            # Constante ajustée de -13.4 à -2.2 pour correspondre aux valeurs officielles
            vfat = 0.134 * self.age + 0.314 * bmi + 0.001410 * self.impedance - 0.145 * height_m - 2.2
        else:
            # Constante femme inchangée (déjà correcte)
            vfat = 0.105 * self.age + 0.275 * bmi + 0.001679 * self.impedance - 0.123 * height_m - 9.8

        vfat = max(1, round(vfat))
        return self.checkValueOverflow(vfat, 1, 30)


    # Get BMI
    def getBMI(self):
        return self.checkValueOverflow(self.weight/((self.height/100)*(self.height/100)), 10, 90)

    # Get ideal weight (just doing a reverse BMI, should be something better)
    def getIdealWeight(self, orig=True):
        if orig and self.sex == 'female':
            return (self.height - 70) * 0.6
        elif orig and self.sex == 'male':
            return (self.height - 80) * 0.7
        else:
            return self.checkValueOverflow((22*self.height)*self.height/10000, 5.5, 198)

    def getFatMassToIdeal(self):
        mass = (self.weight * (self.getFatPercentage() / 100)) - (self.weight * (self.scales.getFatPercentageScale()[2] / 100))
        if mass < 0:
            return {'type': 'to_gain', 'mass': mass*-1}
        else:
            return {'type': 'to_lose', 'mass': mass}

    def getProteinPercentage(self, orig=True):
        if orig:
            proteinPercentage = (self.getMuscleMass() / self.weight) * 100
            proteinPercentage -= self.getWaterPercentage()
        else:
            proteinPercentage = 100 - (floor(self.getFatPercentage() * 100) / 100)
            proteinPercentage -= floor(self.getWaterPercentage() * 100) / 100
            proteinPercentage -= floor((self.getBoneMass()/self.weight*100) * 100) / 100

        return self.checkValueOverflow(proteinPercentage, 5, 32)

    # Remaining methods unchanged
    def getBodyType(self):
        if self.getFatPercentage() > self.scales.getFatPercentageScale()[2]:
            factor = 0
        elif self.getFatPercentage() < self.scales.getFatPercentageScale()[1]:
            factor = 2
        else:
            factor = 1

        if self.getMuscleMass() > self.scales.getMuscleMassScale()[1]:
            return 2 + (factor * 3)
        elif self.getMuscleMass() < self.scales.getMuscleMassScale()[0]:
            return (factor * 3)
        else:
            return 1 + (factor * 3)

    def getMetabolicAge(self):
        if self.sex == 'female':
            metabolicAge = (self.height * -1.1165) + (self.weight * 1.5784) + (self.age * 0.4615) + (self.impedance * 0.0415) + 83.2548
        else:
            metabolicAge = (self.height * -0.7471) + (self.weight * 0.9161) + (self.age * 0.4184) + (self.impedance * 0.0517) + 54.2267
        return self.checkValueOverflow(metabolicAge, 15, 80)
