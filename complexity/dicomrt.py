# Copyright (c) 2009-2016 Aditya Panchal
# Copyright (c) 2009-2010 Roy Keyes
# This class is derived from dicomparser.py of dicompyler-core, released under a BSD license.
#    See the file license.txt included with this distribution, also
#    available at https://github.com/dicompyler/dicompyler-core/
from typing import Dict

import numpy as np
import pydicom as dicom
from pydicom.valuerep import IS


class RTPlan:
    """Class that parses and returns formatted DICOM RT Plan data."""

    def __init__(self, filename: str) -> None:

        if filename:
            self.plan = dict()
            try:
                # Only pydicom 0.9.5 and above supports the force read argument
                if dicom.__version__ >= "0.9.5":
                    self.ds = dicom.read_file(filename, defer_size=100, force=True)
                else:
                    self.ds = dicom.read_file(filename, defer_size=100)
            except (EOFError, IOError):
                # Raise the error for the calling method to handle
                raise
            else:
                # Sometimes DICOM files may not have headers, but they should always
                # have a SOPClassUID to declare what type of file it is. If the
                # file doesn't have a SOPClassUID, then it probably isn't DICOM.
                if "SOPClassUID" not in self.ds:
                    raise AttributeError
        else:
            raise AttributeError

    def get_plan(self) -> Dict[str, str]:
        """Returns the plan information."""
        self.plan["label"] = self.ds.RTPlanLabel
        self.plan["date"] = self.ds.RTPlanDate
        self.plan["time"] = self.ds.RTPlanTime
        self.plan["name"] = ""
        self.plan["rxdose"] = 0.0
        if "DoseReferenceSequence" in self.ds:
            for item in self.ds.DoseReferenceSequence:
                if item.DoseReferenceStructureType == "SITE":
                    self.plan["name"] = "N/A"
                    if "DoseReferenceDescription" in item:
                        self.plan["name"] = item.DoseReferenceDescription
                    if "TargetPrescriptionDose" in item:
                        rxdose = item.TargetPrescriptionDose * 100
                        if rxdose > self.plan["rxdose"]:
                            self.plan["rxdose"] = rxdose
                elif item.DoseReferenceStructureType == "VOLUME":
                    if "TargetPrescriptionDose" in item:
                        self.plan["rxdose"] = item.TargetPrescriptionDose * 100
        if ("FractionGroupSequence" in self.ds) and (self.plan["rxdose"] == 0):
            fg = self.ds.FractionGroupSequence[0]
            if ("ReferencedBeamSequence" in fg) and ("NumberofFractionsPlanned" in fg):
                beams = fg.ReferencedBeamSequence
                fx = fg.NumberofFractionsPlanned
                for beam in beams:
                    if "BeamDose" in beam:
                        self.plan["rxdose"] += beam.BeamDose * fx * 100

        if "FractionGroupSequence" in self.ds:
            fg = self.ds.FractionGroupSequence[0]
            if "ReferencedBeamSequence" in fg:
                self.plan["fractions"] = fg.NumberOfFractionsPlanned
        self.plan["rxdose"] = int(self.plan["rxdose"])

        # referenced beams
        ref_beams = self.get_beams()
        self.plan["beams"] = ref_beams

        # try estimate the number of isocenters
        isos = np.array([ref_beams[i]["IsocenterPosition"] for i in ref_beams])

        # round to 2 decimals
        isos = np.round(isos, 2)
        dist = np.sqrt(np.sum((isos - isos[0]) ** 2, axis=1))
        self.plan["n_isocenters"] = len(np.unique(dist))

        # Total number of MU
        total_mu = np.sum(
            [ref_beams[b]["MU"] for b in ref_beams if "MU" in ref_beams[b]]
        )
        self.plan["Plan_MU"] = total_mu

        tmp = self.get_study_info()
        self.plan["description"] = tmp["description"]
        if "RTPlanName" in self.ds:
            self.plan["plan_name"] = self.ds.RTPlanName
        else:
            self.plan["plan_name"] = ""
        if "PatientsName" in self.ds:
            name = (
                self.ds.PatientsName.family_comma_given()
                .replace(",", "")
                .replace("^", " ")
                .strip()
            )
            self.plan["patient_name"] = name
        else:
            self.plan["patient_name"] = ""
        return self.plan

    def get_beams(self, fx: int = 0) -> Dict[IS, Dict[str, str]]:
        """Return the referenced beams from the specified fraction."""

        beams = {}
        if "BeamSequence" in self.ds:
            bdict = self.ds.BeamSequence
        elif "IonBeamSequence" in self.ds:
            bdict = self.ds.IonBeamSequence
        else:
            return beams
        # Obtain the beam information
        for bi in bdict:
            beam = dict()
            beam["Manufacturer"] = bi.Manufacturer if "Manufacturer" in bi else ""
            beam["InstitutionName"] = (
                bi.InstitutionName if "InstitutionName" in bi else ""
            )
            beam["TreatmentMachineName"] = (
                bi.TreatmentMachineName if "TreatmentMachineName" in bi else ""
            )
            beam["BeamName"] = bi.BeamName if "BeamName" in bi else ""
            beam["SourcetoSurfaceDistance"] = (
                bi.SourcetoSurfaceDistance if "SourcetoSurfaceDistance" in bi else ""
            )
            beam["BeamDescription "] = (
                bi.BeamDescription if "BeamDescription" in bi else ""
            )
            beam["BeamType"] = bi.BeamType if "BeamType" in bi else ""
            beam["RadiationType"] = bi.RadiationType if "RadiationType" in bi else ""
            beam["ManufacturerModelName"] = (
                bi.ManufacturerModelName if "ManufacturerModelName" in bi else ""
            )
            beam["PrimaryDosimeterUnit"] = (
                bi.PrimaryDosimeterUnit if "PrimaryDosimeterUnit" in bi else ""
            )
            beam["NumberofWedges"] = bi.NumberofWedges if "NumberofWedges" in bi else ""
            beam["NumberofCompensators"] = (
                bi.NumberofCompensators if "NumberofCompensators" in bi else ""
            )
            beam["NumberofBoli"] = bi.NumberofBoli if "NumberofBoli" in bi else ""
            beam["NumberofBlocks"] = bi.NumberofBlocks if "NumberofBlocks" in bi else ""
            ftemp = (
                bi.FinalCumulativeMetersetWeight
                if "FinalCumulativeMetersetWeight" in bi
                else ""
            )
            beam["FinalCumulativeMetersetWeight"] = ftemp
            beam["NumberofControlPoints"] = (
                bi.NumberofControlPoints if "NumberofControlPoints" in bi else ""
            )
            beam["TreatmentDeliveryType"] = (
                bi.TreatmentDeliveryType if "TreatmentDeliveryType" in bi else ""
            )

            # adding mlc info from BeamLimitingDeviceSequence
            beam_limits = (
                bi.BeamLimitingDeviceSequence
                if "BeamLimitingDeviceSequence" in bi
                else ""
            )
            beam["BeamLimitingDeviceSequence"] = beam_limits

            # Check control points if exists
            if "ControlPointSequence" in bi:
                beam["ControlPointSequence"] = bi.ControlPointSequence
                # control point 0
                cp0 = bi.ControlPointSequence[0]
                # final control point
                final_cp = bi.ControlPointSequence[-1]

                beam["NominalBeamEnergy"] = (
                    cp0.NominalBeamEnergy if "NominalBeamEnergy" in cp0 else ""
                )
                beam["DoseRateSet"] = cp0.DoseRateSet if "DoseRateSet" in cp0 else ""
                beam["IsocenterPosition"] = (
                    cp0.IsocenterPosition if "IsocenterPosition" in cp0 else ""
                )
                beam["GantryAngle"] = cp0.GantryAngle if "GantryAngle" in cp0 else ""

                # check VMAT delivery
                if "GantryRotationDirection" in cp0:
                    if cp0.GantryRotationDirection != "NONE":

                        # VMAT Delivery
                        beam["GantryRotationDirection"] = (
                            cp0.GantryRotationDirection
                            if "GantryRotationDirection" in cp0
                            else ""
                        )

                        # last control point angle
                        if final_cp.GantryRotationDirection == "NONE":
                            final_angle = (
                                bi.ControlPointSequence[-1].GantryAngle
                                if "GantryAngle" in cp0
                                else ""
                            )
                            beam["GantryFinalAngle"] = final_angle

                btmp = (
                    cp0.BeamLimitingDeviceAngle
                    if "BeamLimitingDeviceAngle" in cp0
                    else ""
                )
                beam["BeamLimitingDeviceAngle"] = btmp
                beam["TableTopEccentricAngle"] = (
                    cp0.TableTopEccentricAngle
                    if "TableTopEccentricAngle" in cp0
                    else ""
                )

                # check beam limits
                if "BeamLimitingDevicePositionSequence" in cp0:
                    for bl in cp0.BeamLimitingDevicePositionSequence:
                        beam[bl.RTBeamLimitingDeviceType] = bl.LeafJawPositions

            # Ion control point sequence
            if "IonControlPointSequence" in bi:
                beam["IonControlPointSequence"] = bi.IonControlPointSequence
                cp0 = bi.IonControlPointSequence[0]
                beam["NominalBeamEnergyUnit"] = (
                    cp0.NominalBeamEnergyUnit if "NominalBeamEnergyUnit" in cp0 else ""
                )
                beam["NominalBeamEnergy"] = (
                    cp0.NominalBeamEnergy if "NominalBeamEnergy" in cp0 else ""
                )
                beam["DoseRateSet"] = cp0.DoseRateSet if "DoseRateSet" in cp0 else ""
                beam["IsocenterPosition"] = (
                    cp0.IsocenterPosition if "IsocenterPosition" in cp0 else ""
                )
                beam["GantryAngle"] = cp0.GantryAngle if "GantryAngle" in cp0 else ""
                btmp1 = (
                    cp0.BeamLimitingDeviceAngle
                    if "BeamLimitingDeviceAngle" in cp0
                    else ""
                )
                beam["BeamLimitingDeviceAngle"] = btmp1

            # add each beam to beams dict
            beams[bi.BeamNumber] = beam

        # Obtain the referenced beam info from the fraction info
        if "FractionGroupSequence" in self.ds:
            fg = self.ds.FractionGroupSequence[fx]
            if "ReferencedBeamSequence" in fg:
                rb = fg.ReferencedBeamSequence
                nfx = fg.NumberOfFractionsPlanned
                for bi in rb:
                    if "BeamDose" in bi:
                        # dose in cGy
                        beams[bi.ReferencedBeamNumber]["dose"] = bi.BeamDose * nfx * 100
                    if "BeamMeterset" in bi:
                        beams[bi.ReferencedBeamNumber]["MU"] = float(bi.BeamMeterset)
        return beams

    def get_study_info(self) -> Dict[str, str]:
        """Return the study information of the current file."""

        study = {}
        if "StudyDescription" in self.ds:
            desc = self.ds.StudyDescription
        else:
            desc = "No description"
        study["description"] = desc
        # Don't assume that every dataset includes a study UID
        study["id"] = self.ds.SeriesInstanceUID
        if "StudyInstanceUID" in self.ds:
            study["id"] = self.ds.StudyInstanceUID

        return study
