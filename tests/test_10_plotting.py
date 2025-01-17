import pytest
import pandas as pd
from matplotlib.figure import Figure
from shapely.geometry import Point, LineString
from plotly.graph_objs import Scattermapbox

from pam.plot.plans import build_person_df, build_cmap, build_person_travel_geodataframe, build_rgb_travel_cmap, \
    plot_travel_plans, plot_activities
from pam.plot.stats import extract_activity_log, extract_leg_log, time_binner, plot_activity_times, plot_leg_times, \
    plot_population_comparisons, calculate_leg_duration_by_mode
from .fixtures import person_heh, Steve, Hilda, instantiate_household_with
from pam.core import Household, Population
from copy import deepcopy
from pam.policy import policies
from tests.test_00_utils import cyclist, pt_person


def test_build_person_dataframe(person_heh):
    df = build_person_df(person_heh)
    assert len(df) == 5
    assert list(df.act) == ['Home', 'Travel', 'Education', 'Travel', 'Home']


def test_build_cmap_dict():
    df = pd.DataFrame(
        [
            {'act': 'Home', 'dur': None},
            {'act': 'Travel', 'dur': None},
            {'act': 'Work', 'dur': None},
            {'act': 'Travel', 'dur': None},
            {'act': 'Home', 'dur': None},
        ]
    )
    cmap = build_cmap(df)
    assert isinstance(cmap, dict)
    assert set(list(cmap)) == set(['Home', 'Work', 'Travel'])


def test_build_rgb_travel_cmap(Steve):
    for leg in Steve.legs:
        leg.start_location.loc = Point(1, 2)
        leg.end_location.loc = Point(2, 3)
    gdf = build_person_travel_geodataframe(Steve)
    cmap = build_rgb_travel_cmap(gdf, colour_by='mode')
    assert cmap == {'car': (255, 237, 111), 'walk': (204, 235, 197)}


def test_build_activity_log(person_heh):
    population = Population()
    for i in range(5):
        hh = Household(i)
        hh.add(person_heh)
        population.add(hh)
    log = extract_activity_log(population)
    assert len(log) == 15
    assert list(log.columns) == ['act', 'start', 'end', 'duration']


def test_build_leg_log(person_heh):
    population = Population()
    for i in range(5):
        hh = Household(i)
        hh.add(person_heh)
        population.add(hh)
    log = extract_leg_log(population)
    assert len(log) == 10
    assert list(log.columns) == ['mode', 'start', 'end', 'duration']


def test_time_binner(person_heh):
    population = Population()
    for i in range(5):
        hh = Household(i)
        hh.add(person_heh)
        population.add(hh)
    log = extract_activity_log(population)
    binned = time_binner(log)
    assert len(binned) == 96
    for h in ['start', 'end', 'duration']:
        assert binned[h].sum() == 3


def test_plot_act_time_bins(Steve, Hilda):
    population = Population()
    for i, person in enumerate([Steve, Hilda]):
        hh = Household(i)
        hh.add(person)
        population.add(hh)
    fig = plot_activity_times(population)
    assert isinstance(fig, Figure)


def test_plot_leg_time_bins(Steve, Hilda):
    population = Population()
    for i, person in enumerate([Steve, Hilda]):
        hh = Household(i)
        hh.add(person)
        population.add(hh)
    fig = plot_leg_times(population)
    assert isinstance(fig, Figure)


def test_plot_population_comparisons(Steve, Hilda):
    population_1 = Population()
    for i, person in enumerate([Steve, Hilda]):
        hh = Household(i)
        hh.add(person)
        population_1.add(hh)
    population_1.name = 'base'
    population_2 = deepcopy(population_1)
    population_2.name = 'work_removed'

    policy_remove_work = policies.RemovePersonActivities(
        activities=['work'],
        probability=1
    )
    policies.apply_policies(population_2, [policy_remove_work])

    list_of_populations = [population_1, population_2]
    outputs = plot_population_comparisons(list_of_populations, 'home')
    legs = outputs[2]
    activities = outputs[3]
    check = calculate_leg_duration_by_mode(population_2)
    assert isinstance(outputs[0], Figure)
    assert isinstance(outputs[1], Figure)
    assert legs.loc['work_removed', 'walk'] == check.loc[check['leg mode'] == 'walk', 'duration_hours'].iloc[0]


def test_plot_travel_plans(cyclist):
    fig = cyclist.plot_travel_plotly(mapbox_access_token='token')
    assert len(fig.data) == 1
    assert isinstance(fig.data[0], Scattermapbox)
    assert fig.data[0].name == 'bike'


def test_plot_travel_plans_coloured_by_purp(pt_person):
    fig = pt_person.plot_travel_plotly(colour_by='pid', mapbox_access_token='token')
    assert len(fig.data) == 1
    assert isinstance(fig.data[0], Scattermapbox)
    assert fig.data[0].name == 'census_1'


def test_plot_travel_plans_grouped_by_legs(pt_person):
    fig = pt_person.plot_travel_plotly(groupby=['seq'], mapbox_access_token='token')
    for dat in fig.data:
        assert isinstance(dat, Scattermapbox)
    assert [dat.name for dat in fig.data] == ["('pt', 3)", "('pt', 5)", "('pt', 7)", "('transit_walk', 1)",
                                              "('transit_walk', 2)", "('transit_walk', 4)", "('transit_walk', 6)",
                                              "('transit_walk', 8)"]


def test_plot_travel_plans_for_household(cyclist, pt_person):
    hhld = instantiate_household_with([cyclist, pt_person])
    fig = hhld.plot_travel_plotly(mapbox_access_token='token')
    assert len(fig.data) == 3
    assert [dat.name for dat in fig.data] == ['bike', 'pt', 'transit_walk']


def test_plot_activities(person_heh):
    df = build_person_df(person_heh)
    try:
        fig = plot_activities(df)
    except (RuntimeError, TypeError, NameError, OSError, ValueError):
        pytest.fail("Error")
