#include <iostream>
#include <fstream>
#include <vector>
#include <cmath>
#include <memory>
#include <limits>
#include <set>
#include <algorithm>

struct Vertex
{
    size_t y, x;
    double h, g;
    std::shared_ptr<Vertex> came_from;
    Vertex(size_t ny, size_t nx)
    {
        y = ny;
        x = nx;
        came_from = nullptr;
        h = g = std::numeric_limits<double>::infinity();
    }

    bool operator<(const Vertex &s) const
    {
        return (h + g) < (s.h + s.g);
    }
};

struct Graph
{
    const char water_mark = '0';
    std::vector<std::vector<std::shared_ptr<Vertex>>> vertexes;
    Graph(): vertexes() {}
    bool create(std::string filename)
    {
        std::fstream mask_file(filename, std::ios_base::in);
        std::string tmp;
        size_t y_count = 0;
        while(std::getline(mask_file, tmp))
        {
            size_t x_count = 0;
            std::vector<std::shared_ptr<Vertex>> row;
            for(auto v: tmp)
            {
                if (v != water_mark)
                    row.push_back(nullptr);
                else
                    row.push_back(std::make_shared<Vertex>(y_count, x_count));
                
                x_count++;
            }
            vertexes.push_back(row);
            y_count++;
        }
        mask_file.close();
    };
    std::vector<std::shared_ptr<Vertex>> incidents(const std::shared_ptr<Vertex> & v) const
    {
        size_t y = v->y;
        size_t x = v->x;
        std::vector<std::shared_ptr<Vertex>> res;
        for(auto i = -1; i <= 1; i++)
            for(auto j = -1; j <= 1; j++)
            {
                if (i == 0 && j == 0)
                    continue;
                
                if (y + i < 0 || y + i >= vertexes.size() || x + j < 0 || x + j >= vertexes[0].size())
                    continue;

                if (vertexes[y + i][x + j] == nullptr) // <========================== may cause out of range :)
                    continue;
                
                res.push_back(vertexes[y + i][x + j]);
            }
        return res;
    }
    std::shared_ptr<Vertex> & operator[](const std::pair<size_t, size_t> & ind)
    {
        return vertexes[ind.first][ind.second];
    }
};

Graph mask;

double h(const std::shared_ptr<Vertex> & goal, const std::shared_ptr<Vertex> & x)
{
    return std::max(std::abs(double(goal->x) - x->x), std::abs(double(goal->y) - x->y));
}
double dist(const std::shared_ptr<Vertex> & fisrt, const std::shared_ptr<Vertex> & second)
{
    return std::sqrt(std::pow(double(fisrt->x) - second->x, 2.0) + std::pow(double(fisrt->y) - second->y, 2.0));
}

bool Astar(std::pair<size_t, size_t> start_ind, std::pair<size_t, size_t> goal_ind)
{
    auto comp = [](const std::shared_ptr<Vertex> &x, const std::shared_ptr<Vertex> &y) {return (*x) < *(y);};
    auto openset = std::multiset<std::shared_ptr<Vertex>, decltype(comp)>(comp);
    std::vector<std::shared_ptr<Vertex>> closedset;

    auto start = mask[start_ind];
    auto goal = mask[goal_ind];

    start->g = 0.0;
    start->h = h(goal, start);
    openset.insert(start);

    while (!openset.empty())
    {
        auto x = *openset.begin();
        if (x == goal)
            return true;
        
        openset.erase(openset.begin());
        closedset.push_back(x);
        
        auto incidents = mask.incidents(x);
        for(auto y: incidents)
        {
            if (std::find(closedset.begin(), closedset.end(), y) != closedset.end())
            {
                continue;
            }

            auto g_score = x->g + dist(x, y);
            
            auto found = std::find(openset.begin(), openset.end(), y);
            if (found == openset.end())
            {
                y->came_from = x;
                y->g = g_score;
                y->h = h(goal, y);
                openset.insert(y);
            }
            else if (g_score < (y->g))
            {
                openset.erase(found);
                y->came_from = x;
                y->g = g_score;
                y->h = h(goal, y);
                openset.insert(y);

            }
        }
    }

    return false;

}

int main(int argc, char *argv[]) 
{
    if (argc < 5)
    {
        std::cout << "Not enought arguments" << std::endl;
    }
    mask.create("mask.txt");
    auto y_b = std::stoi(argv[1]), x_b = std::stoi(argv[2]), y_e = std::stoi(argv[3]), x_e = std::stoi(argv[4]);
    if (mask[{y_b, x_b}] == nullptr)
    {
        std::cout << "Staring vertex is not water" << std::endl;
        return 1;
    }
    if (mask[{y_e, x_e}] == nullptr)
    {
        std::cout << "Finishing vertex is not water" << std::endl;
        return 1;
    }
    auto res = Astar({y_b, x_b}, {y_e, x_e});

    std::cout << res << std::endl;
    if (res)
    {
        std::fstream out("out.txt", std::ios_base::out);
        auto v = mask[{y_e, x_e}];
        while(v->came_from != nullptr)
        {
            out << v->y << " " << v->x << std::endl;
            v = v->came_from;
        }
        out << v->y << " " << v->x << std::endl;
        out.close();
    }
    return 0;
}

