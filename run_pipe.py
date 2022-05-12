from darepype.drp import DataParent
from stonesteps.stepaddkeys import StepAddKeys

inputdata = DataParent(config = 'config.txt')

addkey = StepAddKeys()
addkey(inputdata)