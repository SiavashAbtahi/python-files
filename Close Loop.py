import pandapipes as pp
import numpy as np

from pandapipes.idx_node import PINIT
from pandapipes.idx_branch import MDOTINIT

# Netzwerk erstellen
net = pp.create_empty_network(fluid="water")

# Rohrtyp definieren
typedata = {
    "inner_diameter_mm": 107.1,
    "outer_diameter_mm": 114.3,
    "insulation_thickness_mm": 31.75,
    "material": "P235GH/PUR/PEHD",
    "roughness_mm": 0.2543,
    "u_w_per_m2k": 0.1,
    "type": "heat"
}

pp.create_std_type(net=net, component="pipe", std_type_name="ISOPLUS_DRE100_STD",
                   typedata=typedata, overwrite=True)

# Junctions erstellen
j0 = pp.create_junction(net, pn_bar=4, tfluid_k=293.15, name="junction 0", geodata=(0, 0))
j1 = pp.create_junction(net, pn_bar=4, tfluid_k=293.15, name="junction 1", geodata=(0, 10))
j2 = pp.create_junction(net, pn_bar=4, tfluid_k=293.15, name="junction 2", geodata=(10, 10))
j3 = pp.create_junction(net, pn_bar=4, tfluid_k=293.15, name="junction 3", geodata=(10, 0))

# Zirkulationspumpe
pp.create_circ_pump_const_pressure(net, return_junction=j0, flow_junction=j1,
                                   p_flow_bar=4, plift_bar=1.5, t_flow_k=273.15 + 70,
                                   type="auto", name="const_pressure_pump")

# Wärmeverbraucher
pp.create_heat_consumer(net, from_junction=j2, to_junction=j3,
                        qext_w=10000, controlled_mdot_kg_per_s=2,
                        deltat_k=None, treturn_k=None, type="heat_consumer")

# Vorlaufleitung
pp.create_pipe(net, from_junction=j1, to_junction=j2,
               std_type="ISOPLUS_DRE100_STD", length_km=1,
               k_mm=0.1, loss_coefficient=0,
               sections=100, text_k=283,
               qext_w=0., name="pipe_0_1", type="pipe")

# Rücklaufleitung
pp.create_pipe(net, from_junction=j3, to_junction=j0,
               std_type="ISOPLUS_DRE100_STD", length_km=1,
               k_mm=0.1, loss_coefficient=0,
               sections=100, text_k=283,
               qext_w=0., name="pipe_1_2", type="pipe")

# Hydraulik berechnen
pp.pipeflow(net, stop_condition="tol", iter=100,
            friction_model="colebrook", mode="hydraulics",
            transient=False, nonlinear_method="automatic",
            tol_p=1e-4, tol_m=1e-4)

# Hydraulische Lösung speichern
sol_vec = np.r_[
    net["_pit"]["node"][:, PINIT],
    net["_pit"]["branch"][:, MDOTINIT]
]

# Anfangstemperaturen setzen
net.junction.loc[:, "told_k"] = 293.15
net.junction.loc[:, "tfluid_k"] = 293.15

# Wärmeübergangskoeffizient setzen
net.pipe.loc[:, "u_w_per_m2k"] = 0.1

# Zeiteinstellungen
dt = 60
t_end = 3600

# Transiente Temperaturberechnung
for t in range(dt, t_end + dt, dt):

    pp.pipeflow(net, sol_vec=sol_vec, stop_condition="tol", iter=100,
                friction_model="colebrook", mode="heat",
                transient=True, dt=dt, simulation_time_step=dt,
                ambient_temperature=298.15,
                nonlinear_method="automatic", tol_T=1e-3)

    print("-------------------------")
    print("time =", t, "s")
    print(net.res_junction["t_k"])

    # Temperaturen für nächsten Zeitschritt speichern
    net.junction.loc[:, "told_k"] = net.res_junction["t_k"].values
    net.junction.loc[:, "tfluid_k"] = net.res_junction["t_k"].values