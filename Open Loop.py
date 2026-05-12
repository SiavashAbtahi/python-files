import pandapipes
import numpy as np

from pandapipes.component_models import Pipe
from pandapipes.idx_node import PINIT
from pandapipes.idx_branch import MDOTINIT

# Netzwerk erstellen
net = pandapipes.create_empty_network("net")

# Wasser als Fluid setzen
pandapipes.create_fluid_from_lib(net, "water", overwrite=True)

# Junctions erstellen
junction1 = pandapipes.create_junction(net, pn_bar=3, tfluid_k=293.15, name="Junction 1")
junction2 = pandapipes.create_junction(net, pn_bar=3, tfluid_k=293.15, name="Junction 2")
junction3 = pandapipes.create_junction(net, pn_bar=3, tfluid_k=293.15, name="Junction 3")
junction4 = pandapipes.create_junction(net, pn_bar=3, tfluid_k=293.15, name="Junction 4")

# Externe Quelle
pandapipes.create_ext_grid(net, junction=junction1,
                           p_bar=6, t_k=363.15,
                           name="External Grid", type="pt")

# Verbraucher erstellen
pandapipes.create_sink(net, junction=junction3,
                       mdot_kg_per_s=1, name="Sink 1")

pandapipes.create_sink(net, junction=junction4,
                       mdot_kg_per_s=2, name="Sink 2")

# Rohr 1
pandapipes.create_pipe_from_parameters(net, from_junction=junction1,
                                       to_junction=junction2,
                                       length_km=0.1, diameter_m=0.075,
                                       k_mm=0.025, sections=5,
                                       u_w_per_m2k=100, text_k=298.15,
                                       name="Pipe 1")

# Rohr 2
pandapipes.create_pipe_from_parameters(net, from_junction=junction2,
                                       to_junction=junction3,
                                       length_km=2, diameter_m=0.05,
                                       k_mm=0.025, sections=4,
                                       u_w_per_m2k=100, text_k=298.15,
                                       name="Pipe 2")

# Rohr 3
pandapipes.create_pipe_from_parameters(net, from_junction=junction2,
                                       to_junction=junction4,
                                       length_km=1, diameter_m=0.1,
                                       k_mm=0.025, sections=8,
                                       u_w_per_m2k=50, text_k=298.15,
                                       name="Pipe 3")

# Hydraulik berechnen
pandapipes.pipeflow(
    net,
    mode="hydraulics",
    transient=False,
    stop_condition="tol",
    iter=5,
    friction_model="colebrook",
    nonlinear_method="automatic",
    tol_p=1e-4,
    tol_m=1e-4
)

# Hydraulische Lösung speichern
sol_vec = np.r_[
    net["_pit"]["node"][:, PINIT],
    net["_pit"]["branch"][:, MDOTINIT]
]

# Anfangstemperaturen speichern
net.junction.loc[:, "told_k"] = net.junction["tfluid_k"]

# Wärmeverlust der Rohre
net.pipe.loc[:, "u_w_per_m2k"] = [100.0, 100.0, 50.0]

# Zeitschritt
dt = 60

# Simulationszeit
t_end = 600

# Transiente Temperaturberechnung
for t in range(dt, t_end + dt, dt):

    pandapipes.pipeflow(
        net,
        stop_condition="tol",
        iter=100,
        friction_model="colebrook",
        mode="heat",
        sol_vec=sol_vec,
        transient=True,
        dt=dt,
        simulation_time_step=dt,
        ambient_temperature=298.15,
        nonlinear_method="automatic",
        tol_p=1e-4,
        tol_m=1e-4,
        tol_T=1e-3
    )

    # Interne Temperaturwerte lesen
    pipe_1_results = Pipe.get_internal_results(net, [0])

    # print("-------------------------")
    # print("time =", t, "s")
    #
    # print("TINIT:")
    # print(pipe_1_results["TINIT"])

    print("-------------------------")
    print("time =", t, "s")

    # Junction Temperaturen ausgeben
    print(net.res_junction["t_k"])

    # Temperaturen für nächsten Schritt speichern
    net.junction.loc[:, "told_k"] = net.res_junction["t_k"].values

# Interne Rohrwerte anzeigen
Pipe.get_internal_results(net, [0])