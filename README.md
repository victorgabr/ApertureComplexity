# Aperture Complexity - IMRT/VMAT Plans

It is a Python 3.x port of the Eclipse ESAPI plug-in script. 
As such, it aims to contain the complete functionality of  the aperture complexity analysis.

Since it uses DICOM standard, this module extends the methodology to any TPS that exports DICOM-RP files.

More on misc.py file

## Getting Started

Calculating weighed plan complexity - only IMRT or VMAT.


    python ComplexityScript.py path_to_dicom_RP_file

Plotting aperture complexity per beam aperture using matplotlib.

```python
from complexity.PyComplexityMetric import PyComplexityMetric
from complexity.dicomrt import RTPlan
import matplotlib.pyplot as plt

if __name__ == '__main__':
    # Path to DICOM RTPLAN file - IMRT/VMAT
    pfile = 'RP.dcm'

    # Getting planning data from DICOM file.
    plan_info = RTPlan(filename=pfile)
    plan_dict = plan_info.get_plan()

    # plotting results
    complexity_obj = PyComplexityMetric()
    for k, beam in plan_dict['beams'].items():
        fig, ax = plt.subplots()
        complexity_per_beam_cp = complexity_obj.CalculateForBeamPerAperture(None, plan_dict, beam)
        ax.plot(complexity_per_beam_cp)
        ax.set_xlabel('Control Point')
        ax.set_ylabel('CI [mm-1]')
        txt = 'Beam name: %s  - aperture complexity per control point' % str(k)
        ax.set_title(txt)
        plt.show()
```

Beam 1 - result:

![beam_1_complexity](https://user-images.githubusercontent.com/6777517/37774893-336082a8-2dc0-11e8-9c3f-6b15d8488d9f.png)

      
## Requirements
    pydicom, numpy, pandas, pytest for unit testing
    
## Installing
    python setup.py install

## Contributing

Any bug fixes or improvements are welcome.

## Author
    Victor Gabriel Leandro Alves, D.Sc.
    Copyright 2017-2018
    
## Acknowledgments

University of Michigan, Radiation Oncology
[https://github.com/umro/Complexity]()
