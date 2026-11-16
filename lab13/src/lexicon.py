"""Спільний лексикон: канонічні id, поверхневі форми, закриті словники типів (використовується генератором, нормалізацією та валідацією методу Б)."""
ENT_TYPES = ["PER", "POS", "SKILL", "COURSE", "ORG", "DATE", "CODE"]
REL_TYPES = {"OCCUPIES": ("PER", "POS"), "PROMOTED_TO": ("PER", "POS"), "REQUIRES": ("POS", "SKILL"), "COMPLETED": ("PER", "COURSE"), "TEACHES": ("COURSE", "SKILL"), "PROVIDED_BY": ("COURSE", "ORG"), "HAS_SKILL": ("PER", "SKILL")}
# canon -> список форм (перша — називний відмінок). Частину форм (синоніми) НЕМАЄ в газетирі методу А — це навмисні «невидимі» варіанти.
POS = {"hrManagerPost": ["HR-менеджер", "HR-менеджера", "HR-менеджеру"], "pythonDeveloperPost": ["Python-розробник", "Python-розробника", "Python-розробнику", "бекенд-розробника на Python"],
       "recruiterPost": ["рекрутер", "рекрутера", "рекрутеру", "спеціаліст з підбору персоналу"], "teamLeadPost": ["керівник команди", "керівника команди", "керівнику команди", "тімліда"]}
SKILL = {"pythonProgramming": ["програмування на Python", "Python"], "javaProgramming": ["програмування на Java", "Java"], "hrAnalytics": ["HR-аналітика", "аналітика персоналу"], "sqlDataAnalysis": ["аналіз даних у SQL", "SQL"],
         "labourLaw": ["трудове право"], "dataProtection": ["захист персональних даних"], "negotiation": ["перемовини", "ведення переговорів"], "teamCommunication": ["командна комунікація"],
         "conflictResolution": ["вирішення конфліктів", "медіація"], "coaching": ["коучинг"], "delegation": ["делегування"]}
COURSE = {"negotiationCourse": "Ефективні перемовини", "pythonAdvancedCourse": "Python Advanced", "javaBasics": "Java Basics", "hrAnalyticsPro": "HR Analytics Pro", "sqlForAnalysts": "SQL для аналітиків",
          "labourLawUpdate": "Трудове право: оновлення", "gdprEssentials": "Захист даних (GDPR)", "teamSync": "Командна комунікація", "conflictWorkshop": "Вирішення конфліктів", "coachingSkills": "Коучингові навички",
          "delegationLab": "Практикум з делегування", "pythonBasics": "Python Basics"}
COURSE_SKILL = {"negotiationCourse": "negotiation", "pythonAdvancedCourse": "pythonProgramming", "javaBasics": "javaProgramming", "hrAnalyticsPro": "hrAnalytics", "sqlForAnalysts": "sqlDataAnalysis", "labourLawUpdate": "labourLaw",
                "gdprEssentials": "dataProtection", "teamSync": "teamCommunication", "conflictWorkshop": "conflictResolution", "coachingSkills": "coaching", "delegationLab": "delegation", "pythonBasics": "pythonProgramming"}
ORG = {"prometheus": "Prometheus", "epamUniversity": "EPAM University", "hrSchoolLviv": "Школа HR Lviv", "lawDataCenter": "Центр «Право і Дані»"}
COURSE_ORG = {"negotiationCourse": "hrSchoolLviv", "pythonAdvancedCourse": "epamUniversity", "javaBasics": "epamUniversity", "hrAnalyticsPro": "prometheus", "sqlForAnalysts": "prometheus", "labourLawUpdate": "lawDataCenter",
              "gdprEssentials": "lawDataCenter", "teamSync": "hrSchoolLviv", "conflictWorkshop": "hrSchoolLviv", "coachingSkills": "hrSchoolLviv", "delegationLab": "hrSchoolLviv", "pythonBasics": "prometheus"}
